# -*- coding: utf-8 -*-

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


# =========================
# 3. UTILIDADES GENERALES
# =========================

def query_to_df(sql: str, parameters: Optional[list] = None) -> pd.DataFrame:
    job_config = bigquery.QueryJobConfig(query_parameters=parameters or [])
    rows = bq_client.query(sql, job_config=job_config).result()
    return pd.DataFrame([dict(row) for row in rows])


def json_default(obj: Any):
    return str(obj)


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
        .replace(",", "")
        .replace(".", "")
        .strip()
    )


def seconds_to_mmss(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


STOPWORDS = {
    "que", "qué", "cual", "cuál", "cuales", "cuáles",
    "video", "videos", "capitulo", "capítulo", "capitulos", "capítulos",
    "hablaron", "hablamos", "habla", "mencionaron", "mencionan",
    "sobre", "acerca", "tema", "temas", "del", "de", "la", "el",
    "los", "las", "un", "una", "en", "por", "para", "donde", "dónde",
    "cuando", "cuándo", "minuto", "momento", "relacionados", "relacionado",
    "con", "nuestro", "nuestra", "canal", "dame", "busca", "buscar"
}


def extract_search_terms(text):
    clean = clean_text(text)

    return [
        word for word in re.split(r"\s+", clean)
        if len(word) > 2 and word not in STOPWORDS
    ]


def find_best_transcript_moment(transcript, terms, duration_minutes):
    if not transcript:
        return {
            "moment": "sin minuto",
            "snippet": "No hay transcripción disponible.",
            "matched_term": None,
            "is_estimated": False
        }

    transcript = str(transcript)
    transcript_clean = clean_text(transcript)

    best_index = None
    best_term = None

    for term in terms:
        idx = transcript_clean.find(term)

        if idx != -1 and (best_index is None or idx < best_index):
            best_index = idx
            best_term = term

    if best_index is None:
        return {
            "moment": "aprox. 00:00",
            "snippet": transcript[:600] + ("..." if len(transcript) > 600 else ""),
            "matched_term": None,
            "is_estimated": True
        }

    original_index = min(best_index, len(transcript) - 1)
    start = max(0, original_index - 250)
    end = min(len(transcript), original_index + 450)

    snippet = transcript[start:end].strip()

    if start > 0:
        snippet = "..." + snippet

    if end < len(transcript):
        snippet = snippet + "..."

    if duration_minutes and len(transcript) > 0:
        ratio = original_index / len(transcript)
        estimated_seconds = ratio * float(duration_minutes) * 60
        moment = f"aprox. {seconds_to_mmss(estimated_seconds)}"
    else:
        moment = "aprox. 00:00"

    return {
        "moment": moment,
        "snippet": snippet,
        "matched_term": best_term,
        "is_estimated": True
    }


# =========================
# 4. CAPA BIGQUERY RETRIEVER
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
    def __init__(self, client):
        self.client = client

    def _query(self, sql, parameters=None):
        job_config = bigquery.QueryJobConfig(query_parameters=parameters or [])
        rows = self.client.query(sql, job_config=job_config).result()
        return [dict(row) for row in rows]

    def _video_columns(self):
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

    def _add_filter_clauses(self, clauses, params, filters):
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
            params.append(
                bigquery.ScalarQueryParameter(
                    "duration_type",
                    "STRING",
                    filters.duration_type.lower()
                )
            )

        if filters.has_transcript is not None:
            clauses.append("tiene_transcripcion_valida = @has_transcript")
            params.append(
                bigquery.ScalarQueryParameter(
                    "has_transcript",
                    "BOOL",
                    filters.has_transcript
                )
            )

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
            params.append(
                bigquery.ScalarQueryParameter(
                    "min_engagement",
                    "FLOAT64",
                    filters.min_engagement
                )
            )

    def test_connection(self):
        table = self.client.get_table(TABLE_ID)

        return {
            "tabla": TABLE_ID,
            "filas": table.num_rows,
            "columnas": len(table.schema),
            "schema": [
                {"name": field.name, "type": field.field_type}
                for field in table.schema
            ]
        }

    def channel_profile(self):
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

        rows = self._query(sql, [
            bigquery.ScalarQueryParameter("channel_id", "STRING", CHANNEL_ID)
        ])

        return rows[0] if rows else None

    def analytics_summary(self):
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

        rows = self._query(sql, [
            bigquery.ScalarQueryParameter("channel_id", "STRING", CHANNEL_ID)
        ])

        return rows[0] if rows else None

    def find_video(self, video_reference):
        video_reference = str(video_reference).strip()

        video_id = None

        if re.fullmatch(r"[\w-]{11}", video_reference):
            video_id = video_reference
        else:
            match = re.search(r"(?:v=|youtu\.be/)([\w-]{11})", video_reference)
            if match:
                video_id = match.group(1)

        if video_id:
            sql = f"""
            SELECT {self._video_columns()}
            FROM {QUOTED_TABLE_ID}
            WHERE channel_id = @channel_id
              AND video_id = @video_id
            LIMIT 1
            """

            return self._query(sql, [
                bigquery.ScalarQueryParameter("channel_id", "STRING", CHANNEL_ID),
                bigquery.ScalarQueryParameter("video_id", "STRING", video_id),
            ])

        sql = f"""
        SELECT {self._video_columns()}
        FROM {QUOTED_TABLE_ID}
        WHERE channel_id = @channel_id
          AND LOWER(titulo_video) LIKE @needle
        ORDER BY views DESC
        LIMIT 5
        """

        return self._query(sql, [
            bigquery.ScalarQueryParameter("channel_id", "STRING", CHANNEL_ID),
            bigquery.ScalarQueryParameter(
                "needle",
                "STRING",
                f"%{video_reference.lower()}%"
            ),
        ])

    def search_videos(self, topic, filters=None, order_by="views", limit=8):
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
                params.append(
                    bigquery.ScalarQueryParameter(
                        name,
                        "STRING",
                        f"%{term}%"
                    )
                )

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

    def find_topic_moments(self, topic, filters=None, order_by="views", limit=8):
        rows = self.search_videos(
            topic,
            filters=filters,
            order_by=order_by,
            limit=limit
        )

        terms = extract_search_terms(topic)

        enriched = []

        for row in rows:
            moment = find_best_transcript_moment(
                transcript=row.get("transcripcion_video"),
                terms=terms,
                duration_minutes=row.get("duracion_minutos")
            )

            row["momento_aproximado"] = moment["moment"]
            row["fragmento"] = moment["snippet"]
            row["termino_detectado"] = moment["matched_term"]
            row["momento_estimado"] = moment["is_estimated"]

            enriched.append(row)

        return enriched

    def ranked_videos(self, filters=None, order_by="views", limit=10):
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

    def topic_performance(self, limit=10, order_by="videos"):
        order_map = {
            "videos": "videos DESC",
            "views": "views_totales DESC",
            "likes": "likes_totales DESC",
            "comentarios": "comentarios_totales DESC",
            "engagement": "engagement_promedio DESC",
            "like_rate": "like_rate_promedio DESC",
            "views_por_dia": "views_por_dia_promedio DESC",
        }

        order_sql = order_map.get(order_by, "videos DESC")

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
        ORDER BY {order_sql}
        LIMIT @limit
        """

        return self._query(sql, [
            bigquery.ScalarQueryParameter("channel_id", "STRING", CHANNEL_ID),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
        ])

    def recommendation_context(self, video_reference):
        matches = self.find_video(video_reference)

        if not matches:
            return None

        video = matches[0]

        sql = f"""
        SELECT
          AVG(views) AS avg_views,
          AVG(likes) AS avg_likes,
          AVG(comentarios) AS avg_comentarios,
          AVG(engagement) AS avg_engagement,
          AVG(like_rate) AS avg_like_rate,
          AVG(views_por_dia) AS avg_views_por_dia
        FROM {QUOTED_TABLE_ID}
        WHERE channel_id = @channel_id
          AND formato_video = @formato_video
          AND tema_legible = @tema_legible
        """

        benchmarks = self._query(sql, [
            bigquery.ScalarQueryParameter("channel_id", "STRING", CHANNEL_ID),
            bigquery.ScalarQueryParameter("formato_video", "STRING", video.get("formato_video")),
            bigquery.ScalarQueryParameter("tema_legible", "STRING", video.get("tema_legible")),
        ])

        return {
            "video": video,
            "benchmarks": benchmarks[0] if benchmarks else {}
        }

    def create_ml_model(self):
        sql = f"""
        CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.video_views_model`
        OPTIONS(
          model_type = 'BOOSTED_TREE_REGRESSOR',
          input_label_cols = ['views']
        ) AS
        SELECT
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
          tiene_descripcion
        FROM {QUOTED_TABLE_ID}
        WHERE channel_id = '{CHANNEL_ID}'
          AND views IS NOT NULL
        """

        self.client.query(sql).result()

        return "Modelo BigQuery ML creado correctamente."

    def evaluate_ml_model(self):
        sql = f"""
        SELECT *
        FROM ML.EVALUATE(
          MODEL `{PROJECT_ID}.{DATASET_ID}.video_views_model`
        )
        """

        return self._query(sql)

    def predict_video_performance(self, limit=20, order="underperforming"):
        order_sql = (
            "diferencia_predicha ASC"
            if order == "underperforming"
            else "diferencia_predicha DESC"
        )

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
          MODEL `{PROJECT_ID}.{DATASET_ID}.video_views_model`,
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
            WHERE channel_id = '{CHANNEL_ID}'
          )
        )
        ORDER BY {order_sql}
        LIMIT @limit
        """

        return self._query(sql, [
            bigquery.ScalarQueryParameter("limit", "INT64", limit)
        ])


# =========================
# 5. GEMINI COMO INTERPRETADOR
# =========================

def gemini_generate(prompt, temperature=0.2):
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature
        )
    )

    return response.text


def gemini_json(prompt):
    text = gemini_generate(prompt, temperature=0.1).strip()

    if text.startswith("```json"):
        text = text.replace("```json", "").replace("```", "").strip()
    elif text.startswith("```"):
        text = text.replace("```", "").strip()

    try:
        return json.loads(text)
    except Exception:
        return {
            "intent": "fallback",
            "topic": None,
            "person": None,
            "video_reference": None,
            "order_by": "views",
            "limit": 8,
            "duration_type": None,
            "year": None,
            "month": None,
            "min_views": None,
            "min_likes": None,
            "min_comments": None,
            "min_engagement": None
        }


def interpret_question(question):
    prompt = f"""
Eres el clasificador de intención de un agente RAG para analizar videos de YouTube.

El agente SOLO puede responder sobre:
- videos del canal
- métricas del canal
- títulos, temas y transcripciones
- recomendaciones de contenido
- análisis de interacción
- predicciones de rendimiento con ML

Convierte la pregunta del usuario a JSON válido.

Pregunta:
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
  "limit": numero entero entre 1 y 25,
  "duration_type": "corto | largo | null",
  "year": año o null,
  "month": mes numerico o null,
  "min_views": numero o null,
  "min_likes": numero o null,
  "min_comments": numero o null,
  "min_engagement": numero o null
}}

Reglas:
- "videos relacionados con X" => related_videos.
- "en qué video/capítulo/minuto hablaron de X" => topic_moments.
- "temas más hablados" => topic_analysis con order_by = videos.
- "temas con mejor interacción" => topic_analysis con order_by = engagement.
- "top videos por likes/views/engagement" => ranking.
- "qué mejorarías" => improvements.
- "qué diría X de nuestro canal" => famous_person_opinion.
- "videos que rindieron peor de lo esperado" => ml_underperforming.
- "videos que superaron la predicción" => ml_overperforming.
- Si es externo al canal => out_of_scope.
- Responde SOLO JSON.
"""

    plan = gemini_json(prompt)

    if plan.get("order_by") not in ALLOWED_ORDER_COLUMNS:
        plan["order_by"] = "views"

    try:
        plan["limit"] = max(1, min(int(plan.get("limit") or 8), 25))
    except Exception:
        plan["limit"] = 8

    return plan


def filters_from_plan(plan):
    return SearchFilters(
        year=plan.get("year"),
        month=plan.get("month"),
        duration_type=plan.get("duration_type"),
        min_views=plan.get("min_views"),
        min_likes=plan.get("min_likes"),
        min_comments=plan.get("min_comments"),
        min_engagement=plan.get("min_engagement"),
    )


def generate_final_answer(question, context, tone="claro y amigable"):
    prompt = f"""
Eres un agente conversacional RAG para creadores de contenido de YouTube.

Reglas obligatorias:
- Responde SOLO usando el contexto recuperado.
- No inventes videos, métricas, URLs, fechas ni minutos.
- Si el minuto es aproximado, dilo claramente.
- Si no hay información suficiente, dilo.
- Mantén la respuesta clara, dinámica y amigable.
- Incluye análisis de views, likes, comentarios, engagement y recomendaciones cuando aplique.
- No respondas temas fuera del canal.

Pregunta del usuario:
{question}

Contexto recuperado desde BigQuery y BigQuery ML:
{json.dumps(context, ensure_ascii=False, default=json_default)[:30000]}

Redacta la respuesta final en español:
"""

    return gemini_generate(prompt, temperature=0.35)


# =========================
# 6. AGENTE RAG COMPLETO
# =========================

class RAGYouTubeAgent:
    def __init__(self, retriever):
        self.retriever = retriever

    def answer(self, question):
        plan = interpret_question(question)

        intent = plan.get("intent", "fallback")
        topic = plan.get("topic")
        person = plan.get("person")
        video_reference = plan.get("video_reference")
        order_by = plan.get("order_by", "views")
        limit = plan.get("limit", 8)
        filters = filters_from_plan(plan)

        if intent == "farewell":
            context = {
                "mensaje": "El usuario se despide.",
                "resumen": (
                    "Se trabajó con un agente RAG conectado a BigQuery y Gemini "
                    "para analizar videos, métricas, temas, transcripciones y recomendaciones."
                )
            }
            return generate_final_answer(question, context)

        if intent == "out_of_scope":
            return (
                "Solo puedo responder sobre los videos, métricas, temas, transcripciones, "
                "rendimiento y estrategia del canal cargado en BigQuery."
            )

        if intent == "channel_summary":
            context = {
                "perfil_canal": self.retriever.channel_profile(),
                "metricas_generales": self.retriever.analytics_summary(),
                "temas_mas_hablados": self.retriever.topic_performance(limit=5, order_by="videos"),
                "temas_mejor_interaccion": self.retriever.topic_performance(limit=5, order_by="engagement"),
            }
            return generate_final_answer(question, context)

        if intent == "channel_opinion":
            context = {
                "perfil_canal": self.retriever.channel_profile(),
                "metricas_generales": self.retriever.analytics_summary(),
                "temas_mejor_interaccion": self.retriever.topic_performance(limit=5, order_by="engagement"),
                "videos_mejor_engagement": self.retriever.ranked_videos(order_by="engagement", limit=5),
            }
            return generate_final_answer(question, context)

        if intent == "improvements":
            context = {
                "perfil_canal": self.retriever.channel_profile(),
                "temas_mejor_interaccion": self.retriever.topic_performance(limit=8, order_by="engagement"),
                "videos_mejor_engagement": self.retriever.ranked_videos(order_by="engagement", limit=5),
                "videos_mayor_views_por_minuto": self.retriever.ranked_videos(order_by="views_por_minuto", limit=5),
            }

            try:
                context["videos_peor_de_lo_esperado_ml"] = self.retriever.predict_video_performance(
                    limit=5,
                    order="underperforming"
                )
            except Exception as e:
                context["nota_ml"] = f"No se pudo consultar el modelo ML: {e}"

            return generate_final_answer(question, context)

        if intent == "famous_person_opinion":
            context = {
                "persona": person,
                "nota": (
                    "No es una opinión real de la persona; es una simulación analítica "
                    "basada en su estilo público y datos del canal."
                ),
                "perfil_canal": self.retriever.channel_profile(),
                "metricas_generales": self.retriever.analytics_summary(),
                "temas_mejor_interaccion": self.retriever.topic_performance(limit=5, order_by="engagement"),
                "videos_destacados": self.retriever.ranked_videos(order_by="views", limit=5),
            }
            return generate_final_answer(question, context)

        if intent == "topic_moments":
            if not topic:
                return "No identifiqué el tema que quieres buscar."

            context = {
                "tipo": "busqueda_de_momentos",
                "tema": topic,
                "nota_minutos": (
                    "Los minutos son aproximados porque la transcripción no trae "
                    "timestamps reales por frase."
                ),
                "resultados": self.retriever.find_topic_moments(
                    topic=topic,
                    filters=filters,
                    order_by=order_by,
                    limit=limit
                )
            }
            return generate_final_answer(question, context)

        if intent == "related_videos":
            if not topic:
                return "No identifiqué el tema para buscar videos relacionados."

            context = {
                "tipo": "videos_relacionados",
                "tema": topic,
                "orden": order_by,
                "filtros": filters,
                "resultados": self.retriever.search_videos(
                    topic=topic,
                    filters=filters,
                    order_by=order_by,
                    limit=limit
                )
            }
            return generate_final_answer(question, context)

        if intent == "topic_analysis":
            context = {
                "temas_mas_hablados": self.retriever.topic_performance(limit=limit, order_by="videos"),
                "temas_mejor_interaccion": self.retriever.topic_performance(limit=limit, order_by="engagement"),
                "temas_mas_views": self.retriever.topic_performance(limit=limit, order_by="views"),
            }
            return generate_final_answer(question, context)

        if intent == "ranking":
            context = {
                "tipo": "ranking_videos",
                "orden": order_by,
                "filtros": filters,
                "resultados": self.retriever.ranked_videos(
                    filters=filters,
                    order_by=order_by,
                    limit=limit
                )
            }
            return generate_final_answer(question, context)

        if intent == "video_detail":
            if not video_reference:
                return "No identifiqué el video. Usa video_id, URL o parte del título."

            matches = self.retriever.find_video(video_reference)

            context = {
                "tipo": "detalle_video",
                "referencia": video_reference,
                "resultados": matches
            }
            return generate_final_answer(question, context)

        if intent == "video_recommendations":
            if not video_reference:
                context = {
                    "tipo": "recomendaciones_generales",
                    "videos_mejor_engagement": self.retriever.ranked_videos(
                        order_by="engagement",
                        limit=5
                    ),
                    "temas_mejor_interaccion": self.retriever.topic_performance(
                        limit=5,
                        order_by="engagement"
                    )
                }
            else:
                context = {
                    "tipo": "recomendaciones_video",
                    "video_y_benchmark": self.retriever.recommendation_context(video_reference)
                }

            return generate_final_answer(question, context)

        if intent == "ml_underperforming":
            context = {
                "tipo": "videos_por_debajo_de_lo_esperado",
                "explicacion": "Se comparan views reales contra views predichas por BigQuery ML.",
                "resultados": self.retriever.predict_video_performance(
                    limit=limit,
                    order="underperforming"
                )
            }
            return generate_final_answer(question, context)

        if intent == "ml_overperforming":
            context = {
                "tipo": "videos_que_superaron_prediccion",
                "explicacion": "Se comparan views reales contra views predichas por BigQuery ML.",
                "resultados": self.retriever.predict_video_performance(
                    limit=limit,
                    order="overperforming"
                )
            }
            return generate_final_answer(question, context)

        if intent == "ml_evaluation":
            context = {
                "tipo": "evaluacion_modelo_ml",
                "resultados": self.retriever.evaluate_ml_model()
            }
            return generate_final_answer(question, context)

        context = {
            "tipo": "fallback_busqueda_general",
            "pregunta": question,
            "resultados": self.retriever.search_videos(
                topic=question,
                filters=filters,
                order_by=order_by,
                limit=limit
            )
        }

        return generate_final_answer(question, context)


# =========================
# 7. INICIALIZACIÓN DEL AGENTE
# =========================

@st.cache_resource
def get_agent():
    retriever = BigQueryYouTubeRetriever(bq_client)
    return RAGYouTubeAgent(retriever)


agent = get_agent()
retriever = BigQueryYouTubeRetriever(bq_client)
