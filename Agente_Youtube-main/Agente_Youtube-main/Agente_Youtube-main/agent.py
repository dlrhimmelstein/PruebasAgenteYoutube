# -*- coding: utf-8 -*-

import os
import json
import re
from dataclasses import dataclass
from typing import Optional, Any

import pandas as pd
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
from google import genai
from google.genai import types


# =========================
# 1. CONFIGURACIÓN GENERAL
# =========================

PROJECT_ID = "mineria-datos-493000"
DATASET_ID = "youtube"
TABLE_NAME = "fact_final"
CHANNEL_ID = "UC1Ma6Pwp5F6_W3QFzLt5EdQ"

TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_NAME}"
QUOTED_TABLE_ID = f"`{TABLE_ID}`"

GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_BATCH_SIZE = 100
GEMINI_MODEL = "gemini-2.5-flash"


# =========================
# 2. CLIENTES
# =========================

@st.cache_resource
def get_bigquery_client():
    """
    Crea cliente de BigQuery usando la cuenta de servicio guardada
    en Streamlit Secrets.
    """
    credentials = service_account.Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"])
    )

    return bigquery.Client(
        credentials=credentials,
        project=PROJECT_ID
    )


@st.cache_resource
def get_gemini_client():
    """
    Crea cliente de Gemini usando GOOGLE_API_KEY guardada
    en Streamlit Secrets.
    """
    api_key = st.secrets.get("GOOGLE_API_KEY")

    if not api_key:
        raise ValueError(
            "No se encontró GOOGLE_API_KEY en Streamlit Secrets."
        )

    return genai.Client(api_key=api_key)


bq_client = get_bigquery_client()
gemini_client = get_gemini_client()



def query_to_rows(sql, parameters=None):
    job_config = bigquery.QueryJobConfig(query_parameters=parameters or [])
    rows = bq_client.query(sql, job_config=job_config).result()
    return [dict(row) for row in rows]


def clean_text(text):
    return (
        str(text).lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("¿", "")
        .replace("?", "")
        .replace("¡", "")
        .replace("!", "")
        .strip()
    )


def seconds_to_mmss(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def cosine_similarity(a, b):
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)

    denom = np.linalg.norm(a) * np.linalg.norm(b)

    if denom == 0:
        return 0.0

    return float(np.dot(a, b) / denom)


def json_default(obj):
    return str(obj)

"""#**Generación robusta con Gemini**"""

def gemini_generate(prompt, temperature=0.2, max_retries=2):
    models_to_try = [
        GEMINI_GENERATION_MODEL,
        GEMINI_FALLBACK_MODEL
    ]

    last_error = None

    for model_name in models_to_try:
        for attempt in range(max_retries):
            try:
                response = gemini_client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=temperature
                    )
                )
                return response.text

            except Exception as e:
                last_error = e
                error_text = str(e)

                temporary = (
                    "503" in error_text
                    or "UNAVAILABLE" in error_text
                    or "high demand" in error_text.lower()
                    or "temporarily" in error_text.lower()
                    or "429" in error_text
                    or "RESOURCE_EXHAUSTED" in error_text
                    or "quota" in error_text.lower()
                )

                if not temporary:
                    raise e

                wait_time = (2 ** attempt) + random.uniform(0, 1.5)
                print(f"{model_name} no disponible. Reintentando en {wait_time:.1f}s...")
                time.sleep(wait_time)

        print(f"Cambiando al modelo fallback después de fallar con {model_name}.")

    raise last_error

"""6: Embeddings seguros + caché de preguntas

"""

VECTOR_STORE_PATH = "/content/youtube_transcript_vector_store.pkl"
PARTIAL_VECTOR_STORE_PATH = "/content/youtube_transcript_vector_store_partial.pkl"

EMBEDDING_BATCH_SIZE = 10
EMBEDDING_ITEMS_PER_MINUTE = 80

QUERY_EMBEDDING_CACHE = {}


def embed_texts_safe(texts, task_type="RETRIEVAL_DOCUMENT", batch_size=EMBEDDING_BATCH_SIZE):
    all_embeddings = []

    seconds_per_batch = 60 * (batch_size / EMBEDDING_ITEMS_PER_MINUTE)

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        success = False
        attempt = 0

        while not success:
            try:
                response = gemini_client.models.embed_content(
                    model=GEMINI_EMBEDDING_MODEL,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        task_type=task_type
                    )
                )

                for emb in response.embeddings:
                    all_embeddings.append(list(emb.values))

                success = True

                print(f"Embeddings generados: {min(i + batch_size, len(texts))}/{len(texts)}")

                time.sleep(seconds_per_batch)

            except Exception as e:
                error_text = str(e)

                quota_error = (
                    "429" in error_text
                    or "RESOURCE_EXHAUSTED" in error_text
                    or "quota" in error_text.lower()
                    or "rate" in error_text.lower()
                )

                if not quota_error:
                    raise e

                attempt += 1
                wait_time = min(90, 30 + attempt * 15 + random.uniform(0, 5))

                print(f"Cuota de embeddings alcanzada. Esperando {wait_time:.1f}s y reintentando...")
                time.sleep(wait_time)

    return all_embeddings


def embed_query_safe(query):
    while True:
        try:
            response = gemini_client.models.embed_content(
                model=GEMINI_EMBEDDING_MODEL,
                contents=[query],
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_QUERY"
                )
            )

            return list(response.embeddings[0].values)

        except Exception as e:
            error_text = str(e)

            quota_error = (
                "429" in error_text
                or "RESOURCE_EXHAUSTED" in error_text
                or "quota" in error_text.lower()
                or "rate" in error_text.lower()
            )

            if not quota_error:
                raise e

            print("Cuota alcanzada al vectorizar la pregunta. Esperando 35s...")
            time.sleep(35)


def embed_query_safe_cached(query):
    key = clean_text(query)

    if key in QUERY_EMBEDDING_CACHE:
        return QUERY_EMBEDDING_CACHE[key]

    embedding = embed_query_safe(query)
    QUERY_EMBEDDING_CACHE[key] = embedding

    return embedding

"""Leer videos desde BigQuery"""

def load_videos_from_bigquery():
    sql = f"""
    SELECT
      video_id,
      titulo_video,
      descripcion_video,
      fecha_publicacion,
      duracion_minutos,
      tipo_duracion,
      formato_video,
      views,
      likes,
      comentarios,
      engagement,
      like_rate,
      comment_rate,
      views_por_dia,
      views_por_minuto,
      url_video,
      tema_legible,
      descripcion_segmento,
      transcripcion_video
    FROM {QUOTED_TABLE_ID}
    WHERE channel_id = @channel_id
      AND transcripcion_video IS NOT NULL
      AND tiene_transcripcion_valida = TRUE
    """

    return query_to_rows(
        sql,
        [bigquery.ScalarQueryParameter("channel_id", "STRING", CHANNEL_ID)]
    )


videos = load_videos_from_bigquery()

print("Videos cargados:", len(videos))

"""Segmentar transcripciones"""

def segment_transcript(video, window_words=140, overlap_words=35):
    transcript = str(video.get("transcripcion_video") or "").strip()
    words = transcript.split()

    if not words:
        return []

    total_words = len(words)
    duration_minutes = video.get("duracion_minutos") or 0
    duration_seconds = float(duration_minutes) * 60

    segments = []
    segment_id = 0

    step = max(1, window_words - overlap_words)

    for start_word in range(0, total_words, step):
        end_word = min(start_word + window_words, total_words)
        segment_words = words[start_word:end_word]
        segment_text = " ".join(segment_words).strip()

        if len(segment_text) < 80:
            continue

        start_ratio = start_word / total_words
        end_ratio = end_word / total_words

        estimated_start_seconds = start_ratio * duration_seconds
        estimated_end_seconds = end_ratio * duration_seconds

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
            "estimated_start_seconds": estimated_start_seconds,
            "estimated_end_seconds": estimated_end_seconds,
            "estimated_start_mmss": seconds_to_mmss(estimated_start_seconds),
            "estimated_end_mmss": seconds_to_mmss(estimated_end_seconds),
        })

        segment_id += 1

        if end_word >= total_words:
            break

    return segments


def build_segments(videos):
    all_segments = []

    for video in videos:
        all_segments.extend(segment_transcript(video))

    return all_segments


segments = build_segments(videos)

print("Segmentos creados:", len(segments))

if segments:
    print("Ejemplo:")
    print(segments[0]["titulo_video"])
    print(segments[0]["estimated_start_mmss"], "-", segments[0]["estimated_end_mmss"])
    print(segments[0]["segment_text"][:300])

"""crear o reanudar vector store"""

def build_vector_store_safe(segments, force_rebuild=False, max_segments=None):
    if os.path.exists(VECTOR_STORE_PATH) and not force_rebuild:
        print("Cargando vector store completo desde archivo...")
        with open(VECTOR_STORE_PATH, "rb") as f:
            return pickle.load(f)

    if os.path.exists(PARTIAL_VECTOR_STORE_PATH) and not force_rebuild:
        print("Cargando progreso parcial...")
        with open(PARTIAL_VECTOR_STORE_PATH, "rb") as f:
            vector_store = pickle.load(f)
    else:
        vector_store = []

    selected_segments = segments[:max_segments] if max_segments else segments
    already_done = len(vector_store)

    print(f"Segmentos totales a vectorizar: {len(selected_segments)}")
    print(f"Segmentos ya vectorizados: {already_done}")

    for i in range(already_done, len(selected_segments), EMBEDDING_BATCH_SIZE):
        batch_segments = selected_segments[i:i + EMBEDDING_BATCH_SIZE]

        texts = [
            f"Título: {s['titulo_video']}\n"
            f"Tema clasificado: {s['tema_legible']}\n"
            f"Fragmento: {s['segment_text']}"
            for s in batch_segments
        ]

        embeddings = embed_texts_safe(
            texts,
            task_type="RETRIEVAL_DOCUMENT",
            batch_size=EMBEDDING_BATCH_SIZE
        )

        for segment, embedding in zip(batch_segments, embeddings):
            item = dict(segment)
            item["embedding"] = embedding
            vector_store.append(item)

        with open(PARTIAL_VECTOR_STORE_PATH, "wb") as f:
            pickle.dump(vector_store, f)

        print(f"Progreso guardado: {len(vector_store)}/{len(selected_segments)}")

    with open(VECTOR_STORE_PATH, "wb") as f:
        pickle.dump(vector_store, f)

    print("Vector store completo guardado en:", VECTOR_STORE_PATH)

    return vector_store


vector_store = build_vector_store_safe(
    segments,
    force_rebuild=False,
    max_segments=500
)

print("Segmentos vectorizados:", len(vector_store))

"""10: Búsqueda semántica"""

def semantic_search_segments(query, top_k=8, min_score=0.30):
    query_embedding = embed_query_safe_cached(query)

    scored = []

    for item in vector_store:
        score = cosine_similarity(query_embedding, item["embedding"])

        if score >= min_score:
            row = dict(item)
            row["score_semantico"] = score
            scored.append(row)

    scored = sorted(scored, key=lambda x: x["score_semantico"], reverse=True)

    return scored[:top_k]


def group_best_segments_by_video(results, max_per_video=2):
    grouped = {}
    final = []

    for row in results:
        video_id = row["video_id"]

        if grouped.get(video_id, 0) >= max_per_video:
            continue

        final.append(row)
        grouped[video_id] = grouped.get(video_id, 0) + 1

    return final

"""#**11: Consultas de temas y resumen**"""

def get_channel_summary():
    sql = f"""
    SELECT
      ANY_VALUE(channel_title) AS channel_title,
      COUNT(DISTINCT video_id) AS videos,
      SUM(views) AS views,
      SUM(likes) AS likes,
      SUM(comentarios) AS comentarios,
      AVG(engagement) AS engagement_promedio,
      AVG(like_rate) AS like_rate_promedio,
      AVG(views_por_dia) AS views_por_dia_promedio
    FROM {QUOTED_TABLE_ID}
    WHERE channel_id = @channel_id
    """

    rows = query_to_rows(
        sql,
        [bigquery.ScalarQueryParameter("channel_id", "STRING", CHANNEL_ID)]
    )

    return rows[0] if rows else {}


def get_topic_analysis(limit=10):
    sql_most = f"""
    SELECT
      tema_legible,
      COUNT(DISTINCT video_id) AS videos,
      SUM(views) AS views_totales,
      SUM(likes) AS likes_totales,
      SUM(comentarios) AS comentarios_totales,
      AVG(engagement) AS engagement_promedio,
      AVG(like_rate) AS like_rate_promedio,
      AVG(views_por_dia) AS views_por_dia_promedio
    FROM {QUOTED_TABLE_ID}
    WHERE channel_id = @channel_id
      AND tema_legible IS NOT NULL
    GROUP BY tema_legible
    ORDER BY videos DESC
    LIMIT @limit
    """

    sql_interaction = f"""
    SELECT
      tema_legible,
      COUNT(DISTINCT video_id) AS videos,
      SUM(views) AS views_totales,
      SUM(likes) AS likes_totales,
      SUM(comentarios) AS comentarios_totales,
      AVG(engagement) AS engagement_promedio,
      AVG(like_rate) AS like_rate_promedio,
      AVG(views_por_dia) AS views_por_dia_promedio
    FROM {QUOTED_TABLE_ID}
    WHERE channel_id = @channel_id
      AND tema_legible IS NOT NULL
    GROUP BY tema_legible
    HAVING videos >= 2
    ORDER BY engagement_promedio DESC
    LIMIT @limit
    """

    params = [
        bigquery.ScalarQueryParameter("channel_id", "STRING", CHANNEL_ID),
        bigquery.ScalarQueryParameter("limit", "INT64", limit),
    ]

    return {
        "temas_mas_hablados": query_to_rows(sql_most, params),
        "temas_mejor_interaccion": query_to_rows(sql_interaction, params)
    }

"""12: Respuesta RAG"""

def generate_rag_answer(question, context, response_mode="normal"):
    if response_mode == "momentos":
        instruction = """
Responde de forma breve y directa.
El usuario quiere saber en qué videos se habló del tema y en qué minuto.
NO hagas análisis largo de métricas.
NO des recomendaciones.
Muestra máximo 5 resultados.
Para cada resultado incluye:
- título del video
- minuto aproximado
- fragmento breve
- URL
- views y likes en una sola línea
"""
    else:
        instruction = """
Explica de forma clara, dinámica y amigable.
Si hay métricas, analiza views, likes, comentarios, engagement y like rate.
Si aplica, da recomendaciones accionables.
"""

    prompt = f"""
Eres un agente conversacional RAG para creadores de contenido de YouTube.

Reglas:
- Responde SOLO usando el contexto recuperado.
- No inventes videos, métricas, URLs ni minutos.
- Si el minuto es aproximado, dilo claramente.
- El agente está limitado al canal analizado.
{instruction}

Pregunta del usuario:
{question}

Contexto recuperado:
{json.dumps(context, ensure_ascii=False, default=json_default)[:12000]}

Respuesta en español:
"""

    try:
        return gemini_generate(prompt, temperature=0.25)
    except Exception as e:
        return fallback_semantic_answer(question, context, e, response_mode=response_mode)


def fallback_semantic_answer(question, context, error=None, response_mode="normal"):
    results = context.get("resultados", [])

    if response_mode == "momentos" and results:
        lines = [
            "Gemini no estuvo disponible temporalmente, así que te respondo directamente con los segmentos recuperados.",
            "",
            f"Pregunta: {question}",
            "",
            "Videos donde se menciona el tema:",
            ""
        ]

        for idx, row in enumerate(results[:5], start=1):
            fragmento = str(row.get("segment_text", "")).strip()
            if len(fragmento) > 300:
                fragmento = fragmento[:300] + "..."

            lines.append(
                f"{idx}. {row.get('titulo_video')}\n"
                f"   Minuto aproximado: {row.get('estimated_start_mmss')} - {row.get('estimated_end_mmss')}\n"
                f"   Views: {row.get('views')} | Likes: {row.get('likes')} | Engagement: {row.get('engagement')}\n"
                f"   URL: {row.get('url_video')}\n"
                f"   Fragmento: {fragmento}\n"
            )

        lines.append("Nota: los minutos son aproximados porque la transcripción no tiene timestamps reales por frase.")
        return "\n".join(lines)

    lines = [
        "Gemini no estuvo disponible temporalmente. Te muestro una respuesta directa con los datos recuperados.",
        "",
        f"Pregunta: {question}",
        ""
    ]

    if results:
        lines.append("Segmentos más relevantes:")

        for idx, row in enumerate(results[:5], start=1):
            fragmento = str(row.get("segment_text", "")).strip()
            if len(fragmento) > 400:
                fragmento = fragmento[:400] + "..."

            lines.append(
                f"{idx}. {row.get('titulo_video')}\n"
                f"   Momento aproximado: {row.get('estimated_start_mmss')} - {row.get('estimated_end_mmss')}\n"
                f"   Score semántico: {row.get('score_semantico'):.3f}\n"
                f"   Views: {row.get('views')} | Likes: {row.get('likes')} | Engagement: {row.get('engagement')}\n"
                f"   URL: {row.get('url_video')}\n"
                f"   Fragmento: {fragmento}\n"
            )

    elif "analisis_temas" in context:
        lines.append("Análisis de temas:")

        for idx, row in enumerate(context["analisis_temas"].get("temas_mas_hablados", [])[:5], start=1):
            lines.append(
                f"{idx}. {row.get('tema_legible')} | Videos: {row.get('videos')} | "
                f"Views: {row.get('views_totales')} | Engagement: {row.get('engagement_promedio')}"
            )

        if context["analisis_temas"].get("temas_mejor_interaccion"):
            lines.append("")
            lines.append("Temas con mejor interacción:")

            for idx, row in enumerate(context["analisis_temas"].get("temas_mejor_interaccion", [])[:5], start=1):
                lines.append(
                    f"{idx}. {row.get('tema_legible')} | Videos: {row.get('videos')} | "
                    f"Engagement: {row.get('engagement_promedio')} | Like rate: {row.get('like_rate_promedio')}"
                )

    elif "resumen_canal" in context:
        resumen = context.get("resumen_canal", {})
        lines.append("Resumen del canal:")
        lines.append(f"Canal: {resumen.get('channel_title')}")
        lines.append(f"Videos: {resumen.get('videos')}")
        lines.append(f"Views: {resumen.get('views')}")
        lines.append(f"Likes: {resumen.get('likes')}")
        lines.append(f"Engagement promedio: {resumen.get('engagement_promedio')}")

    else:
        lines.append("No encontré suficiente contexto para responder.")

    if error:
        lines.append("")
        lines.append(f"Detalle técnico: {str(error)[:250]}")

    return "\n".join(lines)

"""#**13: Agente**"""

class SemanticRAGYouTubeAgent:
    def answer(self, question):
        q = clean_text(question)

        if self.is_farewell(q):
            return (
                "Perfecto, lo dejamos aquí por hoy. "
                "El agente quedó diseñado como RAG semántico: recupera segmentos de transcripción vectorizados, "
                "usa BigQuery para métricas y Gemini para redactar respuestas."
            )

        if self.is_out_of_scope(q):
            return (
                "Solo puedo responder sobre videos, transcripciones, métricas, temas y estrategia del canal analizado."
            )

        if self.asks_topic_analysis(q):
            context = {
                "resumen_canal": get_channel_summary(),
                "analisis_temas": get_topic_analysis(limit=10)
            }
            return generate_rag_answer(question, context)

        if self.asks_channel_summary(q):
            context = {
                "resumen_canal": get_channel_summary(),
                "analisis_temas": get_topic_analysis(limit=5)
            }
            return generate_rag_answer(question, context)

        if self.asks_improvements(q):
            context = {
                "resumen_canal": get_channel_summary(),
                "analisis_temas": get_topic_analysis(limit=8),
                "resultados": semantic_search_segments(
                    "momentos con alta interacción humor conversación entretenimiento",
                    top_k=8,
                    min_score=0.25
                )
            }
            return generate_rag_answer(question, context)

        topic = self.extract_topic(question)

        results = semantic_search_segments(
            topic,
            top_k=40,
            min_score=0.18
        )

        results = group_best_segments_by_video(
            results,
            max_per_video=1
        )

        results = results[:5]

        context = {
            "tipo": "busqueda_semantica_en_transcripciones",
            "tema_consultado": topic,
            "nota": "Los momentos son aproximados porque no hay timestamps reales por frase; se estiman por posición del segmento en la transcripción.",
            "resultados": results
        }

        if self.asks_topic_moment(q):
            return generate_rag_answer(question, context, response_mode="momentos")

        return generate_rag_answer(question, context)

    def extract_topic(self, question):
        q = clean_text(question)

        patterns = [
            r"en que video hablaron de\s+(.+)",
            r"en que video hablaron sobre\s+(.+)",
            r"en que videos hablaron de\s+(.+)",
            r"en que videos hablaron sobre\s+(.+)",
            r"en que capitulo hablaron de\s+(.+)",
            r"en que capitulo mencionaron\s+(.+)",
            r"videos relacionados con\s+(.+)",
            r"videos relacionados a\s+(.+)",
            r"videos sobre\s+(.+)",
            r"videos de\s+(.+)",
            r"sobre\s+(.+)",
            r"tema de\s+(.+)",
            r"mencionaron\s+(.+)",
            r"hablaron de\s+(.+)",
            r"hablaron sobre\s+(.+)"
        ]

        for pattern in patterns:
            match = re.search(pattern, q)
            if match:
                return match.group(1).strip()

        return question

    def asks_topic_moment(self, q):
        return any(phrase in q for phrase in [
            "en que video",
            "en que videos",
            "en que capitulo",
            "en que capitulos",
            "en que minuto",
            "en que momento",
            "donde hablaron",
            "cuando mencionaron",
            "hablaron de",
            "hablaron sobre"
        ])

    def asks_topic_analysis(self, q):
        return any(phrase in q for phrase in [
            "temas mas hablados",
            "temas con mejor interaccion",
            "mejor interaccion",
            "analisis de temas",
            "temas funcionan mejor"
        ])

    def asks_channel_summary(self, q):
        return any(phrase in q for phrase in [
            "resumen de que trata",
            "de que trata nuestro canal",
            "resumen del canal",
            "que trata el canal"
        ])

    def asks_improvements(self, q):
        return any(phrase in q for phrase in [
            "que mejorarias",
            "que podemos mejorar",
            "como mejoramos",
            "recomendaciones para mejorar",
            "mejorar el canal"
        ])

    def is_farewell(self, q):
        return any(phrase in q for phrase in [
            "ya no quiero hablar",
            "es todo por hoy",
            "eso es todo",
            "terminamos",
            "adios",
            "bye"
        ])

    def is_out_of_scope(self, q):
        return any(phrase in q for phrase in [
            "clima",
            "bitcoin",
            "presidente",
            "receta",
            "futbol",
            "capital de"
        ])

"""#**inicializar**"""

agent = SemanticRAGYouTubeAgent()

def preguntar(pregunta):
    respuesta = agent.answer(pregunta)
    print(respuesta)

print("Agente RAG semántico listo.")

"""#**PREGUNTAS**"""

def semantic_search_segments(query, top_k=8, min_score=0.30):
    query_embedding = embed_query_safe_cached(query)

    scored = []

    for item in vector_store:
        score = cosine_similarity(query_embedding, item["embedding"])

        if score >= min_score:
            row = dict(item)
            row["score_semantico"] = score
            scored.append(row)

    scored = sorted(scored, key=lambda x: x["score_semantico"], reverse=True)

    return scored[:top_k]


def group_best_segments_by_video(results, max_per_video=2):
    grouped = {}
    final = []

    for row in results:
        video_id = row["video_id"]

        if grouped.get(video_id, 0) >= max_per_video:
            continue

        final.append(row)
        grouped[video_id] = grouped.get(video_id, 0) + 1

    return final

print("Funciones de búsqueda semántica listas.")

preguntar("En qué videoS hablaron de dinero y en qué minuto?")

preguntar("En qué capítulo mencionaron una relación complicada?")

preguntar("Dame un resumen de qué trata nuestro canal")

preguntar("Qué diría MrBeast de nuestro canal")

preguntar("En qué video hablaron sobre familia y en qué minuto")

preguntar("En que video se hablo sobre adicciones")

"""Pruebas de que no hable sobre otros temas que no sean referentes al canal"""

preguntar("En que temporada se hablo del mundial")

preguntar("Como puedo vender palomitas?")
