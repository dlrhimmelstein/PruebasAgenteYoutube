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
    layout="wide",
    initial_sidebar_state="expanded"
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

st.markdown("""
<style>

/* App completa */
[data-testid="stAppViewContainer"] {
    background: #f0f0f0;
}

/* Contenedor principal */
.main .block-container {
    max-width: 1200px;
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}

/* Sidebar fijo */
section[data-testid="stSidebar"] {
    width: 320px !important;
    min-width: 320px !important;
    max-width: 320px !important;
}

/* Evita cambios raros del sidebar */
section[data-testid="stSidebar"] > div {
    width: 320px !important;
}

/* Chat centrado */
[data-testid="stChatMessageContainer"] {
    max-width: 850px;
    margin: auto;
}

/* Input fijo abajo */
[data-testid="stChatInput"] {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-35%);
    width: 700px;
    z-index: 999;
    background: transparent;
}

/* Caja del input */
[data-testid="stChatInput"] textarea {
    border-radius: 20px !important;
    border: 1px solid #d0d0d0 !important;
    background: white !important;
    padding-top: 12px !important;
}

/* Evita que el contenido choque con el input */
.main .block-container {
    padding-bottom: 120px;
}

/* Scroll suave */
html {
    scroll-behavior: smooth;
}

/* Ocultar footer streamlit */
footer {
    visibility: hidden;
}

/* Ocultar menú */
#MainMenu {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)

with st.sidebar:

    st.markdown(
        '<div class="sidebar-title">⚙️ Panel del agente</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sidebar-subtitle">Accesos rápidos</div>',
        unsafe_allow_html=True
    )

    if st.button("🏆  Top videos\nRanking por vistas"):
        st.session_state.prompt_sugerido = (
            "¿Cuáles son mis 5 videos con más vistas?"
        )

    if st.button("📅  Mejor día para publicar\nAnálisis de rendimiento"):
        st.session_state.prompt_sugerido = (
            "¿Qué días son mejores para publicar?"
        )

    if st.button("🎯  Temas más exitosos\nPor engagement"):
        st.session_state.prompt_sugerido = (
            "¿Qué temas tienen más engagement?"
        )

    if st.button("📈  Resumen del canal\nStats generales"):
        st.session_state.prompt_sugerido = (
            "Dame un resumen del canal"
        )

    if st.button("🎬  Formatos que funcionan\nShorts vs podcasts"):
        st.session_state.prompt_sugerido = (
            "¿Qué formatos funcionan mejor?"
        )

    if st.button("❤️  Mayor engagement\nLikes y comentarios"):
        st.session_state.prompt_sugerido = (
            "¿Qué videos tienen mayor engagement?"
        )

    st.divider()

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
    """, unsafe_allow_html=True)

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
