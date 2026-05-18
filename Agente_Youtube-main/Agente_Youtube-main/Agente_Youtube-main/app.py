# -*- coding: utf-8 -*-

import os
import streamlit as st


# =========================
# 1. CONFIGURACIÓN DE PÁGINA
# =========================
# Debe ser el primer comando de Streamlit.
st.set_page_config(
    page_title="Agente YouTube Analytics",
    page_icon="📊",
    layout="centered"
)


# =========================
# 2. CARGA SEGURA DE CREDENCIALES
# =========================
# Esto permite que funcione tanto localmente con .env
# como en Streamlit Cloud con st.secrets.

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# Si existe GOOGLE_API_KEY en Streamlit Secrets,
# también la mandamos a variables de entorno por compatibilidad.
if "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]


if "GOOGLE_API_KEY" not in os.environ or not os.environ["GOOGLE_API_KEY"]:
    st.error("🚨 Error crítico: No se encontró GOOGLE_API_KEY en Secrets o en el archivo .env.")
    st.stop()


if "gcp_service_account" not in st.secrets:
    st.error("🚨 Error crítico: No se encontró gcp_service_account en Streamlit Secrets.")
    st.stop()


# =========================
# 3. IMPORTACIÓN DEL AGENTE
# =========================
# Ya no usamos ADK.
# Importamos el agente RAG propio definido en agent.py.
try:
    from agent import agent, retriever
except Exception as e:
    st.error("🚨 Error al importar el agente desde agent.py.")
    st.exception(e)
    st.stop()


# =========================
# 4. ESTILOS VISUALES
# =========================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

:root {
    --bg-base: #F0F0F0;
    --bg-surface: #F7F7F7;
    --bg-card: #FFFFFF;
    --bg-sidebar: #EBEBEB;
    --border: #E0E0E0;
    --border-dark: #CCCCCC;
    --text-primary: #282828;
    --text-secondary: #666666;
    --text-muted: #999999;
    --yt-red: #E8001C;
    --yt-red-soft: #FFF0F0;
    --yt-red-mid: #FFDDDD;
    --user-bubble: #1A56A8;
    --font-main: 'DM Sans', system-ui, sans-serif;
}

html, body, [class*="css"] {
    font-family: var(--font-main);
}

[data-testid="stAppViewContainer"] {
    background: var(--bg-base);
}

.block-container {
    padding-top: 1rem;
    max-width: 1100px;
}

.custom-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 2px 8px rgba(40,40,40,0.08);
}

.stat-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 6px 13px;
    font-size: 12px;
    color: var(--text-secondary);
    margin-right: 8px;
}

.dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #2BA84A;
    display: inline-block;
}

.yt-red {
    color: var(--yt-red);
}
</style>
""", unsafe_allow_html=True)

# =========================
# 4. ESTILOS VISUALES
# =========================

st.markdown("""
<style>

/* TODO tu CSS grande aquí */

</style>
""", unsafe_allow_html=True)


# ESTE VA JUSTO DEBAJO ↓↓↓

st.markdown("""
<style>
.stMarkdown, .stChatMessage, p, div {
    color: #282828;
}

[data-testid="stChatMessage"] {
    background: transparent;
}

[data-testid="stChatMessageContent"] {
    color: #282828;
}
</style>
""", unsafe_allow_html=True)

# =========================
# ENCABEZADO TIPO YOUTUBE
# =========================

st.markdown("""
<style>
.youtube-header {
    background: #ffffff;
    border-radius: 20px;
    padding: 28px 32px;
    margin-bottom: 24px;
    box-shadow: 0 4px 18px rgba(0,0,0,0.08);
    display: flex;
    align-items: center;
    gap: 18px;
}

.youtube-logo {
    width: 42px;
    height: 30px;
    background: #ff0000;
    border-radius: 9px;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
}

.youtube-title {
    color: #0f0f0f;
    font-size: 25px;
    font-weight: 800;
}

.youtube-subtitle {
    color: #606060;
    font-size: 14px;
    margin-top: 4px;
}
</style>

<div class="youtube-header">
    <div class="youtube-logo">▶</div>
    <div>
        <div class="youtube-title">Agente YouTube Analytics</div>
        <div class="youtube-subtitle">
            Consulta métricas, videos, temas y rendimiento del canal con Gemini + BigQuery
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# =========================
# SIDEBAR TIPO YOUTUBE
# =========================

with st.sidebar:

    st.markdown("""
    <style>

    section[data-testid="stSidebar"] {
        background: #1f1f2e;
        border-right: 1px solid #2b2b3d;
    }

    .sidebar-title {
        color: white;
        font-size: 24px;
        font-weight: 800;
        margin-bottom: 18px;
    }

    .sidebar-subtitle {
        color: #a1a1b5;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 20px;
        margin-bottom: 10px;
    }

    .sidebar-card {
        background: #2a2a3d;
        border-radius: 14px;
        padding: 14px;
        margin-bottom: 10px;
        border: 1px solid #34344a;
    }

    .metric-label {
        color: #b8b8c7;
        font-size: 13px;
    }

    .metric-value {
        color: white;
        font-size: 18px;
        font-weight: 700;
    }

    div.stButton > button {
        width: 100%;
        background: #2a2a3d;
        color: white !important;
        border: 1px solid #3a3a52;
        border-radius: 12px;
        padding: 12px;
        text-align: left;
        font-weight: 600;
        transition: 0.2s;
    }

    div.stButton > button p {
        color: white !important;
        font-weight: 600 !important;
    }

    div.stButton > button span {
        color: white !important;
    }

    div.stButton > button:hover {
        background: #34344a;
        border: 1px solid #4b4b66;
        color: white;
    }

    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="sidebar-title">⚙️ Panel del agente</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sidebar-subtitle">Accesos rápidos</div>',
        unsafe_allow_html=True
    )

    if st.button("🏆 Top videos"):
        st.session_state.prompt_sugerido = (
            "¿Cuáles son mis 5 videos con más vistas?"
        )

    if st.button("📅 Mejor día para publicar"):
        st.session_state.prompt_sugerido = (
            "¿Qué días de la semana son mejores para publicar?"
        )

    if st.button("🎯 Temas más exitosos"):
        st.session_state.prompt_sugerido = (
            "¿Qué temas tienen mejor engagement?"
        )

    if st.button("📈 Resumen del canal"):
        st.session_state.prompt_sugerido = (
            "Dame un resumen general del canal"
        )

    if st.button("🎬 Formatos que funcionan"):
        st.session_state.prompt_sugerido = (
            "¿Qué formatos funcionan mejor en el canal?"
        )

    if st.button("❤️ Mayor engagement"):
        st.session_state.prompt_sugerido = (
            "¿Qué videos tienen mayor engagement?"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        '<div class="sidebar-subtitle">Canal al día</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="sidebar-card">
        <div class="metric-label">Videos</div>
        <div class="metric-value">299</div>
    </div>

    <div class="sidebar-card">
        <div class="metric-label">Views totales</div>
        <div class="metric-value">16.7M</div>
    </div>

    <div class="sidebar-card">
        <div class="metric-label">Likes totales</div>
        <div class="metric-value">716K</div>
    </div>

    <div class="sidebar-card">
        <div class="metric-label">Comentarios</div>
        <div class="metric-value">34.8K</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    if st.button("🗑️ Limpiar conversación"):
        st.session_state.messages = []
        st.rerun()


# =========================
# 7. MENSAJE INFORMATIVO
# =========================

st.markdown(
    """
    <div class="info-box">
        <b>¿Qué puede hacer este agente?</b><br>
        <span class="small-text">
        Puede responder sobre videos, métricas, temas, transcripciones, ranking de contenido,
        recomendaciones y predicciones de rendimiento del canal.
        </span>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================
# 8. MEMORIA DE CONVERSACIÓN
# =========================

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hola 👋 Soy tu agente de análisis de YouTube. "
                "Puedes preguntarme sobre métricas, videos, temas, transcripciones "
                "y recomendaciones del canal."
            )
        }
    ]


# =========================
# 9. MOSTRAR HISTORIAL
# =========================

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# =========================
# 10. CAPTURAR PREGUNTA DEL USUARIO
# =========================

# Input principal
prompt = st.chat_input(
    "Pregunta sobre el canal… ej: ¿De qué hablaron en el episodio 40?"
)

# Si el usuario dio click en un botón del sidebar
if "prompt_sugerido" in st.session_state:
    prompt = st.session_state.prompt_sugerido
    del st.session_state.prompt_sugerido


if prompt:

    # Mostrar mensaje del usuario
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    # Respuesta del agente
    with st.chat_message("assistant"):

        with st.spinner("Consultando BigQuery y generando respuesta..."):

            try:

                respuesta_texto = agent.answer(prompt)

                st.markdown(respuesta_texto)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": respuesta_texto
                    }
                )

            except Exception as e:

                mensaje_error = (
                    "**Ocurrió un error al procesar tu pregunta:**\n\n"
                    f"`{str(e)}`\n\n"
                    "Revisa tus Secrets y permisos de BigQuery."
                )

                st.error(mensaje_error)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": mensaje_error
                    }
                )
