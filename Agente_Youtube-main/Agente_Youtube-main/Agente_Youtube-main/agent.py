# -*- coding: utf-8 -*-

import json
import os
import pickle
import random
import re
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
import streamlit as st
from google import genai
from google.cloud import bigquery
from google.genai import types
from google.oauth2 import service_account


# =========================
# 1. CONFIGURACION GENERAL
# =========================

PROJECT_ID = "mineria-datos-493000"
DATASET_ID = "youtube"
TABLE_NAME = "fact_final"
CHANNEL_ID = "UC1Ma6Pwp5F6_W3QFzLt5EdQ"

TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_NAME}"
QUOTED_TABLE_ID = f"`{TABLE_ID}`"
ML_MODEL_ID = f"`{PROJECT_ID}.{DATASET_ID}.video_views_model`"

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_FALLBACK_MODEL = "gemini-2.5-flash-lite"
GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"

VECTOR_STORE_PATH = Path("youtube_segment_vector_store.pkl")
EMBEDDING_BATCH_SIZE = 10
SEGMENT_WINDOW_WORDS = 140
SEGMENT_OVERLAP_WORDS = 35
MIN_SEMANTIC_SCORE = 0.18
MAX_CONTEXT_CHARS = 12000


# =========================
# 2. CLIENTES
# =========================

@st.cache_resource(show_spinner=False)
def get_bigquery_client() -> bigquery.Client:
    """
    Crea el cliente de BigQuery.
    En Streamlit Cloud usa st.secrets["gcp_service_account"].
    En local puede usar credenciales ADC si no existe ese secret.
    """
    if "gcp_service_account" in st.secrets:
        credentials = service_account.Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"])
        )
        return bigquery.Client(credentials=credentials, project=PROJECT_ID)

    return bigquery.Client(project=PROJECT_ID)


@st.cache_resource(show_spinner=False)
def get_gemini_client() -> genai.Client:
    api_key = st.secrets.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("No se encontro GOOGLE_API_KEY en Secrets ni en variables de entorno.")
    return genai.Client(api_key=api_key)


bq_client = get_bigquery_client()
gemini_client = get_gemini_client()


# =========================
# 3. UTILIDADES
# =========================

def query_to_df(sql: str, parameters: Optional[list] = None) -> pd.DataFrame:
    job_config = bigquery.QueryJobConfig(query_parameters=parameters or [])
    rows = bq_client.query(sql, job_config=job_config).result()
    return pd.DataFrame([dict(row) for row in rows])


def json_default(obj: Any) -> str:
    return str(obj)


def normalize_text(text: Any) -> str:
    text = str(text or "").lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[^\w\s-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def seconds_to_mmss(seconds: float | int | None) -> str:
    seconds = max(0, int(seconds or 0))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def cosine_similarity(a: list[float], b: list[float]) -> float:
    a_arr = np.array(a, dtype=np.float32)
    b_arr = np.array(b, dtype=np.float32)
    denom = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    if denom == 0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / denom)


STOPWORDS = {
    "que", "cual", "cuales", "video", "videos", "capitulo", "capitulos",
    "hablaron", "hablamos", "habla", "mencionaron", "mencionan", "menciono",
    "sobre", "acerca", "tema", "temas", "del", "de", "la", "el", "los",
    "las", "un", "una", "en", "por", "para", "donde", "cuando", "minuto",
    "momento", "relacionados", "relacionado", "con", "nuestro", "nuestra",
    "canal", "dame", "busca", "buscar", "ordenados", "ordenado", "cerca",
}


def extract_search_terms(text: str) -> list[str]:
    return [
        word for word in normalize_text(text).split()
        if len(word) > 2 and word not in STOPWORDS
    ]


def compact_history(history: Optional[list[dict[str, str]]], max_chars: int = 1600) -> str:
    if not history:
        return "Sin historial reciente."

    lines = []
    for message in history[-6:]:
        role = message.get("role", "user")
        content = str(message.get("content", "")).strip()
        if content:
            lines.append(f"{role}: {content[:350]}")

    return "\n".join(lines)[-max_chars:] or "Sin historial reciente."


def extract_topic_from_question(question: str) -> str:
    q = normalize_text(question)
    patterns = [
        r"en que videos? (?:se )?(?:hablo|hablaron|mencionaron|menciona|trate|trataron) (?:de|sobre)?\s*(.+)",
        r"en que capitulos? (?:se )?(?:mencionaron|hablaron|hablo) (?:de|sobre)?\s*(.+)",
        r"en que minutos? (?:se )?(?:mencionaron|hablaron|hablo) (?:de|sobre)?\s*(.+)",
        r"donde (?:se )?(?:hablo|hablaron|mencionaron) (?:de|sobre)?\s*(.+)",
        r"videos relacionados (?:con|a)\s+(.+)",
        r"videos? sobre\s+(.+)",
        r"(?:hablaron|hablo|mencionaron|mencione) (?:de|sobre)\s+(.+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            topic = match.group(1).strip()
            topic = re.sub(r"\b(y en que minuto|minuto|video|videos|capitulo|capitulos)\b", " ", topic)
            return re.sub(r"\s+", " ", topic).strip()

    terms = extract_search_terms(question)
    return " ".join(terms[:8]) if terms else question.strip()


def infer_topic_from_history(history: Optional[list[dict[str, str]]]) -> Optional[str]:
    if not history:
        return None

    for message in reversed(history[-8:]):
        if message.get("role") != "user":
            continue
        topic = extract_topic_from_question(message.get("content", ""))
        terms = extract_search_terms(topic)
        if terms:
            return " ".join(terms[:8])

    return None


# =========================
# 4. BIGQUERY RETRIEVER
# =========================

ALLOWED_ORDER_COLUMNS = {
    "views": "views",
    "likes": "likes",
    "comentarios": "comentarios",
    "engagement": "engagement",
    "like_rate": "like_rate",
    "views_por_dia": "views_por_dia",
    "views_por_minuto": "views_por_minuto",
    "fecha": "fecha_publicacion",
}


@dataclass(frozen=True)
class SearchFilters:
    year: Optional[int] = None
    month: Optional[int] = None
    duration_type: Optional[str] = None
    has_transcript: Optional[bool] = None
    min_views: Optional[int] = None
    min_likes: Optional[int] = None
    min_comments: Optional[int] = None
    min_engagement: Optional[float] = None


class BigQueryYouTubeRetriever:
    def __init__(self, client: bigquery.Client):
        self.client = client

    def _query(self, sql: str, parameters: Optional[list] = None) -> list[dict[str, Any]]:
        job_config = bigquery.QueryJobConfig(query_parameters=parameters or [])
        rows = self.client.query(sql, job_config=job_config).result()
        return [dict(row) for row in rows]

    def _video_columns(self) -> str:
        return """
          video_id,
          titulo_video,
          descripcion_video,
          fecha_publicacion,
          categoria_nombre,
          duracion_minutos,
          tipo_duracion,
          views,
          likes,
          comentarios,
          engagement,
          like_rate,
          comment_rate,
          views_por_dia,
          likes_por_1000_views,
          comentarios_por_1000_views,
          views_por_minuto,
          url_video,
          tema_legible,
          descripcion_segmento,
          formato_video,
          transcripcion_video
        """

    def _add_filter_clauses(
        self,
        clauses: list[str],
        params: list[bigquery.QueryParameter],
        filters: Optional[SearchFilters],
    ) -> None:
        if not filters:
            return
        if filters.year:
            clauses.append("anio_publicacion = @year")
            params.append(bigquery.ScalarQueryParameter("year", "INT64", filters.year))
        if filters.month:
            clauses.append("mes_publicacion = @month")
            params.append(bigquery.ScalarQueryParameter("month", "INT64", filters.month))
        if filters.duration_type:
            clauses.append("LOWER(tipo_duracion) = @duration_type")
            params.append(bigquery.ScalarQueryParameter("duration_type", "STRING", filters.duration_type.lower()))
        if filters.has_transcript is not None:
            clauses.append("tiene_transcripcion_valida = @has_transcript")
            params.append(bigquery.ScalarQueryParameter("has_transcript", "BOOL", filters.has_transcript))
        if filters.min_views:
            clauses.append("views >= @min_views")
            params.append(bigquery.ScalarQueryParameter("min_views", "INT64", filters.min_views))
        if filters.min_likes:
            clauses.append("likes >= @min_likes")
            params.append(bigquery.ScalarQueryParameter("min_likes", "INT64", filters.min_likes))
        if filters.min_comments:
            clauses.append("comentarios >= @min_comments")
            params.append(bigquery.ScalarQueryParameter("min_comments", "INT64", filters.min_comments))
        if filters.min_engagement:
            clauses.append("engagement >= @min_engagement")
            params.append(bigquery.ScalarQueryParameter("min_engagement", "FLOAT64", filters.min_engagement))

    def test_connection(self) -> dict[str, Any]:
        table = self.client.get_table(TABLE_ID)
        return {
            "tabla": TABLE_ID,
            "filas": table.num_rows,
            "columnas": len(table.schema),
            "schema": [{"name": field.name, "type": field.field_type} for field in table.schema],
        }

    def load_videos_with_transcript(self) -> list[dict[str, Any]]:
        sql = f"""
        SELECT {self._video_columns()}
        FROM {QUOTED_TABLE_ID}
        WHERE channel_id = @channel_id
          AND transcripcion_video IS NOT NULL
          AND LENGTH(TRIM(transcripcion_video)) > 50
        """
        return self._query(sql, [bigquery.ScalarQueryParameter("channel_id", "STRING", CHANNEL_ID)])

    def channel_profile(self) -> Optional[dict[str, Any]]:
        sql = f"""
        SELECT
          ANY_VALUE(channel_title) AS channel_title,
          ANY_VALUE(channel_id) AS channel_id,
          MAX(suscriptores_canal) AS suscriptores_canal,
          MAX(total_videos_canal) AS total_videos_canal,
          MAX(total_views_canal) AS total_views_canal,
          COUNT(DISTINCT video_id) AS videos_en_tabla,
          MIN(fecha_publicacion) AS primer_video,
          MAX(fecha_publicacion) AS ultimo_video
        FROM {QUOTED_TABLE_ID}
        WHERE channel_id = @channel_id
        """
        rows = self._query(sql, [bigquery.ScalarQueryParameter("channel_id", "STRING", CHANNEL_ID)])
        return rows[0] if rows else None

    def analytics_summary(self) -> Optional[dict[str, Any]]:
        sql = f"""
        SELECT
          COUNT(DISTINCT video_id) AS videos,
          SUM(views) AS views,
          SUM(likes) AS likes,
          SUM(comentarios) AS comentarios,
          AVG(engagement) AS engagement_promedio,
          AVG(like_rate) AS like_rate_promedio,
          AVG(views_por_dia) AS views_por_dia_promedio,
          AVG(views_por_minuto) AS views_por_minuto_promedio
        FROM {QUOTED_TABLE_ID}
        WHERE channel_id = @channel_id
        """
        rows = self._query(sql, [bigquery.ScalarQueryParameter("channel_id", "STRING", CHANNEL_ID)])
        return rows[0] if rows else None

    def search_videos(
        self,
        topic: str,
        filters: Optional[SearchFilters] = None,
        order_by: str = "views",
        limit: int = 8,
    ) -> list[dict[str, Any]]:
        terms = extract_search_terms(topic)
        order_col = ALLOWED_ORDER_COLUMNS.get(order_by, "views")
        params = [
            bigquery.ScalarQueryParameter("channel_id", "STRING", CHANNEL_ID),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
        ]
        clauses = ["channel_id = @channel_id"]

        if terms:
            term_clauses = []
            for idx, term in enumerate(terms[:8]):
                name = f"term_{idx}"
                term_clauses.append(f"""
                LOWER(CONCAT(
                  IFNULL(titulo_video, ''), ' ',
                  IFNULL(descripcion_video, ''), ' ',
                  IFNULL(transcripcion_video, ''), ' ',
                  IFNULL(tema_legible, ''), ' ',
                  IFNULL(descripcion_segmento, '')
                )) LIKE @{name}
                """)
                params.append(bigquery.ScalarQueryParameter(name, "STRING", f"%{term}%"))
            clauses.append("(" + " OR ".join(term_clauses) + ")")

        self._add_filter_clauses(clauses, params, filters)
        sql = f"""
        SELECT {self._video_columns()}
        FROM {QUOTED_TABLE_ID}
        WHERE {" AND ".join(clauses)}
        ORDER BY {order_col} DESC
        LIMIT @limit
        """
        return self._query(sql, params)

    def ranked_videos(
        self,
        filters: Optional[SearchFilters] = None,
        order_by: str = "views",
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        order_col = ALLOWED_ORDER_COLUMNS.get(order_by, "views")
        params = [
            bigquery.ScalarQueryParameter("channel_id", "STRING", CHANNEL_ID),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
        ]
        clauses = ["channel_id = @channel_id"]
        self._add_filter_clauses(clauses, params, filters)
        sql = f"""
        SELECT {self._video_columns()}
        FROM {QUOTED_TABLE_ID}
        WHERE {" AND ".join(clauses)}
        ORDER BY {order_col} DESC
        LIMIT @limit
        """
        return self._query(sql, params)

    def topic_performance(self, limit: int = 10, order_by: str = "videos") -> list[dict[str, Any]]:
        order_map = {
            "videos": "videos DESC",
            "views": "views_totales DESC",
            "likes": "likes_totales DESC",
            "comentarios": "comentarios_totales DESC",
            "engagement": "engagement_promedio DESC",
            "like_rate": "like_rate_promedio DESC",
            "views_por_dia": "views_por_dia_promedio DESC",
        }
        sql = f"""
        SELECT
          tema_legible,
          COUNT(DISTINCT video_id) AS videos,
          SUM(views) AS views_totales,
          SUM(likes) AS likes_totales,
          SUM(comentarios) AS comentarios_totales,
          AVG(engagement) AS engagement_promedio,
          AVG(like_rate) AS like_rate_promedio,
          AVG(views_por_dia) AS views_por_dia_promedio,
          AVG(views_por_minuto) AS views_por_minuto_promedio
        FROM {QUOTED_TABLE_ID}
        WHERE channel_id = @channel_id
          AND tema_legible IS NOT NULL
        GROUP BY tema_legible
        ORDER BY {order_map.get(order_by, "videos DESC")}
        LIMIT @limit
        """
        return self._query(sql, [
            bigquery.ScalarQueryParameter("channel_id", "STRING", CHANNEL_ID),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
        ])

    def evaluate_ml_model(self) -> list[dict[str, Any]]:
        sql = f"SELECT * FROM ML.EVALUATE(MODEL {ML_MODEL_ID})"
        return self._query(sql)

    def predict_video_performance(self, limit: int = 10, order: str = "underperforming") -> list[dict[str, Any]]:
        order_sql = "diferencia_predicha ASC" if order == "underperforming" else "diferencia_predicha DESC"
        sql = f"""
        SELECT
          predicted_views,
          titulo_video,
          views AS views_reales,
          views - predicted_views AS diferencia_predicha,
          likes,
          comentarios,
          engagement,
          like_rate,
          tema_legible,
          formato_video,
          url_video
        FROM ML.PREDICT(
          MODEL {ML_MODEL_ID},
          (
            SELECT
              titulo_video,
              views,
              likes,
              comentarios,
              engagement,
              like_rate,
              comment_rate,
              views_por_suscriptor,
              duracion_minutos,
              edad_video_dias,
              anio_publicacion,
              mes_publicacion,
              dia_publicacion,
              dia_semana_publicacion,
              tipo_duracion,
              formato_video,
              tema_legible,
              tiene_transcripcion_valida,
              tiene_descripcion,
              url_video
            FROM {QUOTED_TABLE_ID}
            WHERE channel_id = @channel_id
          )
        )
        ORDER BY {order_sql}
        LIMIT @limit
        """
        return self._query(sql, [
            bigquery.ScalarQueryParameter("channel_id", "STRING", CHANNEL_ID),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
        ])


# =========================
# 5. EMBEDDINGS Y SEGMENTOS
# =========================

def segment_transcript(
    video: dict[str, Any],
    window_words: int = SEGMENT_WINDOW_WORDS,
    overlap_words: int = SEGMENT_OVERLAP_WORDS,
) -> list[dict[str, Any]]:
    transcript = str(video.get("transcripcion_video") or "").strip()
    words = transcript.split()
    if not words:
        return []

    total_words = len(words)
    duration_seconds = float(video.get("duracion_minutos") or 0) * 60
    step = max(1, window_words - overlap_words)
    segments = []

    for segment_id, start_word in enumerate(range(0, total_words, step)):
        end_word = min(start_word + window_words, total_words)
        segment_text = " ".join(words[start_word:end_word]).strip()
        if len(segment_text) < 80:
            continue

        start_seconds = (start_word / total_words) * duration_seconds if duration_seconds else 0
        end_seconds = (end_word / total_words) * duration_seconds if duration_seconds else 0
        search_blob = " ".join([
            str(video.get("titulo_video") or ""),
            str(video.get("tema_legible") or ""),
            str(video.get("descripcion_segmento") or ""),
            segment_text,
        ])

        segments.append({
            "segment_id": segment_id,
            "video_id": video.get("video_id"),
            "titulo_video": video.get("titulo_video"),
            "url_video": video.get("url_video"),
            "fecha_publicacion": video.get("fecha_publicacion"),
            "duracion_minutos": video.get("duracion_minutos"),
            "tipo_duracion": video.get("tipo_duracion"),
            "formato_video": video.get("formato_video"),
            "views": video.get("views"),
            "likes": video.get("likes"),
            "comentarios": video.get("comentarios"),
            "engagement": video.get("engagement"),
            "like_rate": video.get("like_rate"),
            "comment_rate": video.get("comment_rate"),
            "views_por_dia": video.get("views_por_dia"),
            "views_por_minuto": video.get("views_por_minuto"),
            "tema_legible": video.get("tema_legible"),
            "descripcion_segmento": video.get("descripcion_segmento"),
            "segment_text": segment_text,
            "search_blob_norm": normalize_text(search_blob),
            "estimated_start_seconds": start_seconds,
            "estimated_end_seconds": end_seconds,
            "estimated_start_mmss": seconds_to_mmss(start_seconds),
            "estimated_end_mmss": seconds_to_mmss(end_seconds),
        })

        if end_word >= total_words:
            break

    return segments


def build_segments(videos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    segments = []
    for video in videos:
        segments.extend(segment_transcript(video))
    return segments


def embed_texts_safe(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[i:i + EMBEDDING_BATCH_SIZE]

        for attempt in range(5):
            try:
                response = gemini_client.models.embed_content(
                    model=GEMINI_EMBEDDING_MODEL,
                    contents=batch,
                    config=types.EmbedContentConfig(task_type=task_type),
                )
                all_embeddings.extend([list(emb.values) for emb in response.embeddings])
                break
            except Exception as exc:
                error_text = str(exc).lower()
                temporary = any(token in error_text for token in [
                    "429", "503", "quota", "rate", "resource_exhausted", "unavailable", "temporar",
                ])
                if not temporary or attempt == 4:
                    raise
                time.sleep(min(90, 20 + attempt * 15 + random.uniform(0, 3)))

    return all_embeddings


@st.cache_data(show_spinner=False, ttl=3600)
def embed_query_cached(query: str) -> list[float]:
    response = gemini_client.models.embed_content(
        model=GEMINI_EMBEDDING_MODEL,
        contents=[query],
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )
    return list(response.embeddings[0].values)


def build_vector_store(retriever: BigQueryYouTubeRetriever) -> list[dict[str, Any]]:
    videos = retriever.load_videos_with_transcript()
    segments = build_segments(videos)
    max_segments = st.secrets.get("MAX_INDEX_SEGMENTS")
    if max_segments:
        segments = segments[: int(max_segments)]

    vector_store = []
    progress = st.progress(0, text="Construyendo indice semantico de transcripciones...")
    total = max(1, len(segments))

    for i in range(0, len(segments), EMBEDDING_BATCH_SIZE):
        batch_segments = segments[i:i + EMBEDDING_BATCH_SIZE]
        texts = [
            f"Titulo: {s['titulo_video']}\n"
            f"Tema clasificado: {s.get('tema_legible')}\n"
            f"Descripcion: {s.get('descripcion_segmento')}\n"
            f"Fragmento de transcripcion: {s['segment_text']}"
            for s in batch_segments
        ]
        embeddings = embed_texts_safe(texts, task_type="RETRIEVAL_DOCUMENT")

        for segment, embedding in zip(batch_segments, embeddings):
            item = dict(segment)
            item["embedding"] = embedding
            vector_store.append(item)

        progress.progress(min(1.0, len(vector_store) / total), text=f"Indexando segmentos {len(vector_store)}/{total}")

    progress.empty()
    payload = {
        "table_id": TABLE_ID,
        "channel_id": CHANNEL_ID,
        "created_at": time.time(),
        "segment_count": len(vector_store),
        "items": vector_store,
    }
    try:
        with VECTOR_STORE_PATH.open("wb") as file:
            pickle.dump(payload, file)
    except OSError:
        pass

    return vector_store


@st.cache_resource(show_spinner=False)
def get_vector_store(force_rebuild: bool = False) -> list[dict[str, Any]]:
    retriever = BigQueryYouTubeRetriever(bq_client)

    if VECTOR_STORE_PATH.exists() and not force_rebuild:
        try:
            with VECTOR_STORE_PATH.open("rb") as file:
                payload = pickle.load(file)
            if payload.get("table_id") == TABLE_ID and payload.get("channel_id") == CHANNEL_ID:
                return payload.get("items", [])
        except Exception:
            pass

    return build_vector_store(retriever)


def filters_match_segment(row: dict[str, Any], filters: Optional[SearchFilters]) -> bool:
    if not filters:
        return True
    if filters.duration_type and normalize_text(row.get("tipo_duracion")) != normalize_text(filters.duration_type):
        return False
    if filters.min_views and (row.get("views") or 0) < filters.min_views:
        return False
    if filters.min_likes and (row.get("likes") or 0) < filters.min_likes:
        return False
    if filters.min_comments and (row.get("comentarios") or 0) < filters.min_comments:
        return False
    if filters.min_engagement and (row.get("engagement") or 0) < filters.min_engagement:
        return False
    return True


def semantic_search_segments(
    vector_store: list[dict[str, Any]],
    query: str,
    filters: Optional[SearchFilters] = None,
    top_k: int = 30,
    min_score: float = MIN_SEMANTIC_SCORE,
) -> list[dict[str, Any]]:
    query_embedding = embed_query_cached(normalize_text(query))
    query_terms = extract_search_terms(query)
    scored = []

    for item in vector_store:
        if not filters_match_segment(item, filters):
            continue
        semantic_score = cosine_similarity(query_embedding, item["embedding"])
        matched_terms = [term for term in query_terms if term in item.get("search_blob_norm", "")]
        lexical_boost = min(0.08, 0.02 * len(matched_terms))
        final_score = semantic_score + lexical_boost

        if semantic_score >= min_score or matched_terms:
            row = dict(item)
            row["score_semantico"] = semantic_score
            row["score_final"] = final_score
            row["terminos_detectados"] = matched_terms
            scored.append(row)

    return sorted(scored, key=lambda row: row["score_final"], reverse=True)[:top_k]


def group_best_segments_by_video(
    results: list[dict[str, Any]],
    max_per_video: int = 1,
    limit: int = 5,
) -> list[dict[str, Any]]:
    grouped: dict[str, int] = {}
    final = []

    for row in results:
        video_id = row.get("video_id")
        if grouped.get(video_id, 0) >= max_per_video:
            continue
        final.append(row)
        grouped[video_id] = grouped.get(video_id, 0) + 1
        if len(final) >= limit:
            break

    return final


# =========================
# 6. GEMINI
# =========================

def gemini_generate(prompt: str, temperature: float = 0.2, max_retries: int = 3) -> str:
    last_error = None
    for model_name in [GEMINI_MODEL, GEMINI_FALLBACK_MODEL]:
        for attempt in range(max_retries):
            try:
                response = gemini_client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=temperature),
                )
                return response.text or ""
            except Exception as exc:
                last_error = exc
                error_text = str(exc).lower()
                temporary = any(token in error_text for token in [
                    "429", "503", "quota", "rate", "resource_exhausted", "unavailable", "temporar",
                ])
                if not temporary or attempt == max_retries - 1:
                    break
                time.sleep(min(45, 8 + attempt * 10 + random.uniform(0, 2)))

    raise last_error or RuntimeError("No se pudo generar respuesta con Gemini.")


def default_intent_plan() -> dict[str, Any]:
    return {
        "intent": "fallback",
        "topic": None,
        "person": None,
        "video_reference": None,
        "order_by": "views",
        "limit": 5,
        "duration_type": None,
        "year": None,
        "month": None,
        "min_views": None,
        "min_likes": None,
        "min_comments": None,
        "min_engagement": None,
        "has_transcript": None,
    }


def normalize_intent_plan(plan: Any) -> dict[str, Any]:
    if not isinstance(plan, dict):
        return default_intent_plan()

    normalized = default_intent_plan()
    normalized.update(plan)

    allowed_intents = {
        "farewell", "channel_summary", "channel_opinion", "improvements",
        "famous_person_opinion", "topic_moments", "topic_analysis",
        "related_videos", "ranking", "video_detail", "video_recommendations",
        "ml_underperforming", "ml_overperforming", "ml_evaluation",
        "out_of_scope", "fallback",
    }
    if normalized["intent"] not in allowed_intents:
        normalized["intent"] = "fallback"

    if normalized["order_by"] not in ALLOWED_ORDER_COLUMNS:
        normalized["order_by"] = "views"

    try:
        normalized["limit"] = max(1, min(int(normalized.get("limit") or 5), 10))
    except Exception:
        normalized["limit"] = 5

    for key in ["year", "month", "min_views", "min_likes", "min_comments"]:
        try:
            if normalized.get(key) is not None:
                normalized[key] = int(normalized[key])
        except Exception:
            normalized[key] = None

    try:
        if normalized.get("min_engagement") is not None:
            normalized["min_engagement"] = float(normalized["min_engagement"])
    except Exception:
        normalized["min_engagement"] = None

    if normalized.get("duration_type") not in {"corto", "largo", None}:
        normalized["duration_type"] = None

    if normalized.get("has_transcript") not in {True, False, None}:
        normalized["has_transcript"] = None

    return normalized


def gemini_json(prompt: str) -> dict[str, Any]:
    try:
        text = gemini_generate(prompt, temperature=0.1).strip()
        text = re.sub(r"^```(?:json)?", "", text).replace("```", "").strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)
        return normalize_intent_plan(json.loads(text))
    except Exception:
        return default_intent_plan()


def interpret_question(question: str, history: Optional[list[dict[str, str]]] = None) -> dict[str, Any]:
    prompt = f"""
Eres el clasificador de intencion de un agente RAG para analizar videos de YouTube.
Convierte la pregunta del usuario a JSON valido.

Historial reciente:
{compact_history(history)}

Pregunta actual:
{question}

Intenciones permitidas:
- farewell
- channel_summary
- channel_opinion
- improvements
- famous_person_opinion
- topic_moments
- topic_analysis
- related_videos
- ranking
- video_detail
- video_recommendations
- ml_underperforming
- ml_overperforming
- ml_evaluation
- out_of_scope
- fallback

Campos:
{{
  "intent": "...",
  "topic": "tema principal o null",
  "person": "persona famosa o null",
  "video_reference": "video_id, url o titulo si existe, si no null",
  "order_by": "views | likes | comentarios | engagement | like_rate | views_por_dia | views_por_minuto | fecha",
  "limit": numero entero entre 1 y 10,
  "duration_type": "corto | largo | null",
  "year": anio o null,
  "month": mes numerico o null,
  "min_views": numero o null,
  "min_likes": numero o null,
  "min_comments": numero o null,
  "min_engagement": numero o null,
  "has_transcript": true | false | null
}}

Reglas:
- "en que video/capitulo/minuto/momento hablaron de X" => topic_moments.
- "videos relacionados con X" => related_videos.
- "temas mas hablados" => topic_analysis con order_by = videos.
- "temas con mejor interaccion" => topic_analysis con order_by = engagement.
- "top videos por likes/views/engagement" => ranking.
- "que mejorarias" => improvements.
- "videos que rindieron peor de lo esperado" => ml_underperforming.
- "videos que superaron la prediccion" => ml_overperforming.
- Si es externo al canal => out_of_scope.
- Responde SOLO JSON.
"""
    plan = gemini_json(prompt)
    q = normalize_text(question)

    if any(phrase in q for phrase in [
        "en que video", "en que videos", "en que capitulo", "en que minuto",
        "en que momento", "donde hablaron", "donde hable", "cuando mencionaron",
    ]):
        plan["intent"] = "topic_moments"
        plan["topic"] = plan.get("topic") or extract_topic_from_question(question) or infer_topic_from_history(history)
        plan["has_transcript"] = True

    if plan.get("intent") in {"topic_moments", "related_videos"} and not plan.get("topic"):
        plan["topic"] = extract_topic_from_question(question) or infer_topic_from_history(history)

    return normalize_intent_plan(plan)


def filters_from_plan(plan: dict[str, Any]) -> SearchFilters:
    return SearchFilters(
        year=plan.get("year"),
        month=plan.get("month"),
        duration_type=plan.get("duration_type"),
        has_transcript=plan.get("has_transcript"),
        min_views=plan.get("min_views"),
        min_likes=plan.get("min_likes"),
        min_comments=plan.get("min_comments"),
        min_engagement=plan.get("min_engagement"),
    )


def compact_context(context: dict[str, Any], max_chars: int = MAX_CONTEXT_CHARS) -> str:
    return json.dumps(context, ensure_ascii=False, default=json_default)[:max_chars]


def generate_final_answer(
    question: str,
    context: dict[str, Any],
    history: Optional[list[dict[str, str]]] = None,
    response_mode: str = "normal",
) -> str:
    if response_mode == "moments":
        extra_rules = """
- Responde breve y contundente.
- Muestra maximo 5 resultados.
- Para cada resultado incluye titulo, minuto aproximado, fragmento breve y URL.
- Menciona views y likes solo como apoyo, sin analisis largo.
- No agregues recomendaciones si el usuario solo pregunto donde se hablo del tema.
"""
    else:
        extra_rules = """
- Responde claro, breve y accionable.
- Si hay metricas, usa views, likes, comentarios, engagement y like rate solo cuando aporten valor.
- Evita parrafos largos.
"""

    prompt = f"""
Eres un agente conversacional RAG para creadores de contenido de YouTube.

Reglas obligatorias:
- Responde SOLO usando el contexto recuperado.
- No inventes videos, metricas, URLs, fechas ni minutos.
- Si el minuto es aproximado, dilo claramente.
- Si no hay informacion suficiente, dilo.
- No respondas temas fuera del canal.
{extra_rules}

Historial reciente:
{compact_history(history, max_chars=1000)}

Pregunta del usuario:
{question}

Contexto recuperado:
{compact_context(context)}

Redacta la respuesta final en espanol:
"""
    try:
        return gemini_generate(prompt, temperature=0.25)
    except Exception as exc:
        return fallback_answer_without_gemini(question, context, exc)


def fallback_answer_without_gemini(question: str, context: dict[str, Any], error: Exception) -> str:
    lines = [
        "Gemini no estuvo disponible temporalmente. Te dejo una respuesta directa con lo recuperado:",
        "",
    ]

    if context.get("resultados"):
        for idx, row in enumerate(context["resultados"][:5], start=1):
            fragment = row.get("segment_text") or row.get("fragmento") or ""
            if len(fragment) > 300:
                fragment = fragment[:300] + "..."
            lines.append(
                f"{idx}. {row.get('titulo_video', 'Sin titulo')}\n"
                f"   Minuto aprox.: {row.get('estimated_start_mmss', '00:00')} - {row.get('estimated_end_mmss', '')}\n"
                f"   Views: {row.get('views', 'N/A')} | Likes: {row.get('likes', 'N/A')}\n"
                f"   URL: {row.get('url_video', 'Sin URL')}\n"
                f"   Fragmento: {fragment}\n"
            )
    else:
        lines.append("No encontre resultados suficientes en el contexto recuperado.")

    lines.append(f"\nDetalle tecnico resumido: {str(error)[:180]}")
    return "\n".join(lines)


# =========================
# 7. AGENTE RAG HIBRIDO
# =========================

class RAGYouTubeAgent:
    def __init__(self, retriever: BigQueryYouTubeRetriever, vector_store: list[dict[str, Any]]):
        self.retriever = retriever
        self.vector_store = vector_store

    def answer(self, question: str, history: Optional[list[dict[str, str]]] = None) -> str:
        plan = interpret_question(question, history=history)
        intent = plan.get("intent", "fallback")
        topic = plan.get("topic") or extract_topic_from_question(question) or infer_topic_from_history(history)
        filters = filters_from_plan(plan)
        order_by = plan.get("order_by", "views")
        limit = plan.get("limit", 5)

        if intent == "farewell":
            return "Listo. El agente queda preparado para seguir analizando el canal cuando lo necesites."

        if intent == "out_of_scope":
            return "Solo puedo responder sobre videos, transcripciones, metricas, temas, rendimiento y estrategia del canal cargado en BigQuery."

        if intent == "channel_summary":
            context = {
                "perfil_canal": self.retriever.channel_profile(),
                "metricas_generales": self.retriever.analytics_summary(),
                "temas_mas_hablados": self.retriever.topic_performance(limit=5, order_by="videos"),
                "temas_mejor_interaccion": self.retriever.topic_performance(limit=5, order_by="engagement"),
            }
            return generate_final_answer(question, context, history=history)

        if intent in {"channel_opinion", "famous_person_opinion"}:
            context = {
                "persona": plan.get("person"),
                "nota": "Si se menciona una persona famosa, es una simulacion analitica, no una opinion real.",
                "perfil_canal": self.retriever.channel_profile(),
                "metricas_generales": self.retriever.analytics_summary(),
                "temas_mejor_interaccion": self.retriever.topic_performance(limit=5, order_by="engagement"),
                "videos_destacados": self.retriever.ranked_videos(order_by="views", limit=5),
            }
            return generate_final_answer(question, context, history=history)

        if intent == "improvements":
            context = {
                "perfil_canal": self.retriever.channel_profile(),
                "temas_mejor_interaccion": self.retriever.topic_performance(limit=8, order_by="engagement"),
                "videos_mejor_engagement": self.retriever.ranked_videos(order_by="engagement", limit=5),
                "videos_mayor_views_por_minuto": self.retriever.ranked_videos(order_by="views_por_minuto", limit=5),
            }
            return generate_final_answer(question, context, history=history)

        if intent == "topic_moments":
            if not topic:
                return "No identifique el tema que quieres buscar en las transcripciones."

            results = semantic_search_segments(
                self.vector_store,
                topic,
                filters=filters,
                top_k=40,
                min_score=MIN_SEMANTIC_SCORE,
            )
            results = group_best_segments_by_video(results, max_per_video=1, limit=min(limit, 5))

            if not results:
                lexical = self.retriever.search_videos(topic, filters=filters, order_by=order_by, limit=min(limit, 5))
                results = [self._lexical_video_to_segment(row, topic) for row in lexical]

            context = {
                "tipo": "busqueda_semantica_segmentada_en_transcripciones",
                "tema_consultado": topic,
                "nota_minutos": "Los minutos son aproximados porque la transcripcion no trae timestamps reales por frase.",
                "resultados": results,
            }
            return generate_final_answer(question, context, history=history, response_mode="moments")

        if intent == "related_videos":
            if not topic:
                return "No identifique el tema para buscar videos relacionados."

            semantic = semantic_search_segments(self.vector_store, topic, filters=filters, top_k=30)
            semantic = group_best_segments_by_video(semantic, max_per_video=1, limit=limit)
            lexical = self.retriever.search_videos(topic, filters=filters, order_by=order_by, limit=limit)
            context = {
                "tipo": "videos_relacionados_hibridos",
                "tema": topic,
                "resultados_semanticos_por_segmento": semantic,
                "resultados_lexicos_bigquery": lexical,
            }
            return generate_final_answer(question, context, history=history)

        if intent == "topic_analysis":
            context = {
                "temas_mas_hablados": self.retriever.topic_performance(limit=limit, order_by="videos"),
                "temas_mejor_interaccion": self.retriever.topic_performance(limit=limit, order_by="engagement"),
                "temas_mas_views": self.retriever.topic_performance(limit=limit, order_by="views"),
            }
            return generate_final_answer(question, context, history=history)

        if intent == "ranking":
            context = {
                "tipo": "ranking_videos",
                "orden": order_by,
                "filtros": filters,
                "resultados": self.retriever.ranked_videos(filters=filters, order_by=order_by, limit=limit),
            }
            return generate_final_answer(question, context, history=history)

        if intent == "ml_underperforming":
            context = {
                "tipo": "videos_por_debajo_de_lo_esperado",
                "resultados": self.retriever.predict_video_performance(limit=limit, order="underperforming"),
            }
            return generate_final_answer(question, context, history=history)

        if intent == "ml_overperforming":
            context = {
                "tipo": "videos_que_superaron_prediccion",
                "resultados": self.retriever.predict_video_performance(limit=limit, order="overperforming"),
            }
            return generate_final_answer(question, context, history=history)

        if intent == "ml_evaluation":
            context = {"tipo": "evaluacion_modelo_ml", "resultados": self.retriever.evaluate_ml_model()}
            return generate_final_answer(question, context, history=history)

        context = {
            "tipo": "fallback_hibrido",
            "pregunta": question,
            "tema_detectado": topic,
            "resultados_semanticos": group_best_segments_by_video(
                semantic_search_segments(self.vector_store, topic or question, filters=filters, top_k=25),
                max_per_video=1,
                limit=5,
            ),
            "resultados_bigquery": self.retriever.search_videos(topic or question, filters=filters, order_by=order_by, limit=5),
        }
        return generate_final_answer(question, context, history=history)

    def _lexical_video_to_segment(self, row: dict[str, Any], topic: str) -> dict[str, Any]:
        transcript = str(row.get("transcripcion_video") or "")
        terms = extract_search_terms(topic)
        clean_transcript = normalize_text(transcript)

        best_word_index = 0
        for term in terms:
            char_index = clean_transcript.find(term)
            if char_index >= 0:
                best_word_index = max(0, len(clean_transcript[:char_index].split()) - 20)
                break

        words = transcript.split()
        snippet_words = words[best_word_index:best_word_index + 120] if words else []
        snippet = " ".join(snippet_words) if snippet_words else str(row.get("descripcion_segmento") or "")
        ratio = best_word_index / max(1, len(words))
        start_seconds = ratio * float(row.get("duracion_minutos") or 0) * 60

        item = dict(row)
        item.update({
            "segment_text": snippet,
            "estimated_start_seconds": start_seconds,
            "estimated_end_seconds": start_seconds + 45,
            "estimated_start_mmss": seconds_to_mmss(start_seconds),
            "estimated_end_mmss": seconds_to_mmss(start_seconds + 45),
            "score_semantico": None,
            "score_final": None,
            "terminos_detectados": terms,
        })
        return item


# =========================
# 8. INICIALIZACION
# =========================

@st.cache_resource(show_spinner=False)
def get_retriever() -> BigQueryYouTubeRetriever:
    return BigQueryYouTubeRetriever(bq_client)


@st.cache_resource(show_spinner=False)
def get_agent() -> RAGYouTubeAgent:
    retriever = get_retriever()
    vector_store = get_vector_store(force_rebuild=False)
    return RAGYouTubeAgent(retriever, vector_store)


def rebuild_semantic_index() -> int:
    get_vector_store.clear()
    get_agent.clear()
    vector_store = get_vector_store(force_rebuild=True)
    return len(vector_store)


retriever = get_retriever()
agent = get_agent()
