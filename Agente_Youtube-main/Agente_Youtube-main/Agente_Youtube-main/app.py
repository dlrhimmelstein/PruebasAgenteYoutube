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
 
with st.sidebar:
 
    st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
 
    <style>
 
    section[data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: 1px solid #e5e5e5 !important;
    }
 
    section[data-testid="stSidebar"] > div:first-child {
        padding: 0 !important;
    }
 
    /* ---- HEADER ---- */
    .yt-sb-header {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 16px 16px 12px;
        border-bottom: 1px solid #f0f0f0;
        margin-bottom: 0;
    }
    .yt-sb-logo {
        width: 34px;
        height: 34px;
        background: #ff0000;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .yt-sb-logo svg { width: 18px; height: 18px; fill: white; }
    .yt-sb-channel { font-size: 13px; font-weight: 600; color: #111; line-height: 1.3; }
    .yt-sb-powered  { font-size: 11px; color: #888; line-height: 1.3; }
 
    /* ---- SECTION LABEL ---- */
    .yt-sb-label {
        padding: 12px 16px 4px;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: #aaa;
        text-transform: uppercase;
    }
 
    /* ---- MENU ITEMS ---- */
    .yt-sb-item {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 8px 16px;
        cursor: pointer;
        transition: background 0.12s;
    }
    .yt-sb-item:hover { background: #f5f5f5; }
 
    .yt-sb-icon {
        width: 30px;
        height: 30px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        font-size: 15px;
    }
    .ic-orange { background: #fff3e0; color: #e65c00; }
    .ic-blue   { background: #e3f2fd; color: #1565c0; }
    .ic-green  { background: #e8f5e9; color: #2e7d32; }
    .ic-purple { background: #f3e5f5; color: #6a1b9a; }
    .ic-teal   { background: #e0f2f1; color: #00695c; }
    .ic-pink   { background: #fce4ec; color: #880e4f; }
    .ic-yellow { background: #fffde7; color: #f57f17; }
    .ic-red    { background: #ffebee; color: #b71c1c; }
 
    .yt-sb-item-title { font-size: 13px; font-weight: 500; color: #111; line-height: 1.3; }
    .yt-sb-item-sub   { font-size: 11px; color: #888; line-height: 1.3; }
 
    /* ---- DIVIDER ---- */
    .yt-sb-divider { height: 1px; background: #f0f0f0; margin: 6px 0; }
 
    /* ---- STATS BOX ---- */
    .yt-sb-stats {
        margin: 8px 12px 12px;
        background: #f9f9f9;
        border-radius: 10px;
        padding: 12px 14px;
        border: 1px solid #efefef;
    }
    .yt-sb-stats-title {
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: #aaa;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .yt-sb-stat-row {
        display: flex;
        justify-content: space-between;
        padding: 3px 0;
        font-size: 12px;
    }
    .yt-sb-stat-label { color: #777; }
    .yt-sb-stat-val   { font-weight: 600; color: #111; }
    .yt-sb-status-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 4px 0;
    }
    .yt-sb-dot {
        display: inline-block;
        width: 7px; height: 7px;
        border-radius: 50%;
        background: #22c55e;
        margin-right: 5px;
    }
    .yt-sb-status-label { font-size: 12px; color: #777; }
    .yt-sb-status-val   { font-size: 12px; font-weight: 600; color: #22c55e; }
 
    /* Ocultar botones nativos de Streamlit en sidebar */
    section[data-testid="stSidebar"] div.stButton > button {
        display: none;
    }
 
    </style>
 
    <!-- HEADER -->
    <div class="yt-sb-header">
        <div class="yt-sb-logo">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M19.59 7a2.5 2.5 0 0 0-1.76-1.76C16.46 5 12 5 12 5s-4.46 0-5.83.24A2.5 2.5 0 0 0 4.41 7 26 26 0 0 0 4.17 12a26 26 0 0 0 .24 5 2.5 2.5 0 0 0 1.76 1.76C7.54 19 12 19 12 19s4.46 0 5.83-.24A2.5 2.5 0 0 0 19.59 17 26 26 0 0 0 19.83 12a26 26 0 0 0-.24-5zM10 15v-6l5 3-5 3z"/>
            </svg>
        </div>
        <div>
            <div class="yt-sb-channel">Las Damitas Histeria</div>
            <div class="yt-sb-powered">Agente de análisis · Powered by Gemini</div>
        </div>
    </div>
 
    <!-- ACCESOS RÁPIDOS -->
    <div class="yt-sb-label">Accesos rápidos</div>
 
    <div class="yt-sb-item">
        <div class="yt-sb-icon ic-orange"><i class="ti ti-trophy"></i></div>
        <div>
            <div class="yt-sb-item-title">Top videos</div>
            <div class="yt-sb-item-sub">Ranking por vistas</div>
        </div>
    </div>
 
    <div class="yt-sb-item">
        <div class="yt-sb-icon ic-blue"><i class="ti ti-calendar-stats"></i></div>
        <div>
            <div class="yt-sb-item-title">Mejor día para publicar</div>
            <div class="yt-sb-item-sub">Análisis de rendimiento</div>
        </div>
    </div>
 
    <div class="yt-sb-item">
        <div class="yt-sb-icon ic-green"><i class="ti ti-flame"></i></div>
        <div>
            <div class="yt-sb-item-title">Temas más exitosos</div>
            <div class="yt-sb-item-sub">Por engagement</div>
        </div>
    </div>
 
    <div class="yt-sb-item">
        <div class="yt-sb-icon ic-purple"><i class="ti ti-chart-bar"></i></div>
        <div>
            <div class="yt-sb-item-title">Resumen del canal</div>
            <div class="yt-sb-item-sub">Stats generales</div>
        </div>
    </div>
 
    <div class="yt-sb-item">
        <div class="yt-sb-icon ic-teal"><i class="ti ti-layout-grid"></i></div>
        <div>
            <div class="yt-sb-item-title">Formatos que funcionan</div>
            <div class="yt-sb-item-sub">Shorts vs podcasts</div>
        </div>
    </div>
 
    <div class="yt-sb-item">
        <div class="yt-sb-icon ic-pink"><i class="ti ti-heart"></i></div>
        <div>
            <div class="yt-sb-item-title">Mayor engagement</div>
            <div class="yt-sb-item-sub">Likes y comentarios</div>
        </div>
    </div>
 
    <div class="yt-sb-divider"></div>
 
    <!-- BUSCAR VIDEO -->
    <div class="yt-sb-label">Buscar video</div>
 
    <div class="yt-sb-item">
        <div class="yt-sb-icon ic-blue"><i class="ti ti-search"></i></div>
        <div>
            <div class="yt-sb-item-title">Buscar por tema</div>
            <div class="yt-sb-item-sub">¿En qué ep hablaron de X?</div>
        </div>
    </div>
 
    <div class="yt-sb-item">
        <div class="yt-sb-icon ic-yellow"><i class="ti ti-video"></i></div>
        <div>
            <div class="yt-sb-item-title">Analizar video</div>
            <div class="yt-sb-item-sub">Por título o URL</div>
        </div>
    </div>
 
    <div class="yt-sb-divider"></div>
 
    <!-- STATS -->
    <div class="yt-sb-stats">
        <div class="yt-sb-stats-title">Canal al día</div>
        <div class="yt-sb-stat-row">
            <span class="yt-sb-stat-label">Videos</span>
            <span class="yt-sb-stat-val">299</span>
        </div>
        <div class="yt-sb-stat-row">
            <span class="yt-sb-stat-label">Views totales</span>
            <span class="yt-sb-stat-val">16.7M</span>
        </div>
        <div class="yt-sb-stat-row">
            <span class="yt-sb-stat-label">Likes totales</span>
            <span class="yt-sb-stat-val">716K</span>
        </div>
        <div class="yt-sb-stat-row">
            <span class="yt-sb-stat-label">Comentarios</span>
            <span class="yt-sb-stat-val">34.8K</span>
        </div>
        <div class="yt-sb-divider" style="margin: 6px 0;"></div>
        <div class="yt-sb-status-row">
            <span class="yt-sb-status-label">
                <span class="yt-sb-dot"></span>Estado del agente
            </span>
            <span class="yt-sb-status-val">Activo</span>
        </div>
    </div>
 
    """, unsafe_allow_html=True)
 
    # ---- Botones invisibles (mantienen la funcionalidad) ----
    if st.button("Top videos", key="btn_top"):
        st.session_state.prompt_sugerido = "¿Cuáles son mis 5 videos con más vistas?"
 
    if st.button("Mejor día para publicar", key="btn_dia"):
        st.session_state.prompt_sugerido = "¿Qué días de la semana son mejores para publicar?"
 
    if st.button("Temas más exitosos", key="btn_temas"):
        st.session_state.prompt_sugerido = "¿Qué temas tienen mejor engagement?"
 
    if st.button("Resumen del canal", key="btn_resumen"):
        st.session_state.prompt_sugerido = "Dame un resumen general del canal"
 
    if st.button("Formatos que funcionan", key="btn_formatos"):
        st.session_state.prompt_sugerido = "¿Qué formatos funcionan mejor en el canal?"
 
    if st.button("Mayor engagement", key="btn_engagement"):
        st.session_state.prompt_sugerido = "¿Qué videos tienen mayor engagement?"
 
    if st.button("Limpiar conversación", key="btn_limpiar"):
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
