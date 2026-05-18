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
.yt-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 0 18px 0;
    border-bottom: 2px solid #ff0000;
    margin-bottom: 20px;
}
.yt-header-logo {
    width: 36px;
    height: 36px;
    background: #ff0000;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.yt-header-logo svg { width: 20px; height: 20px; fill: white; }
.yt-header-title {
    font-size: 18px;
    font-weight: 700;
    color: #0f0f0f;
    line-height: 1.2;
}
.yt-header-sub {
    font-size: 12px;
    color: #888;
    margin-top: 2px;
}
.yt-header-badge {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: #555;
    background: #f2f2f2;
    padding: 5px 12px;
    border-radius: 20px;
}
.yt-header-badge .dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: #22c55e;
    display: inline-block;
}
</style>

<div class="yt-header">
    <div class="yt-header-logo">
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M19.59 7a2.5 2.5 0 0 0-1.76-1.76C16.46 5 12 5 12 5s-4.46 0-5.83.24A2.5 2.5 0 0 0 4.41 7 26 26 0 0 0 4.17 12a26 26 0 0 0 .24 5 2.5 2.5 0 0 0 1.76 1.76C7.54 19 12 19 12 19s4.46 0 5.83-.24A2.5 2.5 0 0 0 19.59 17 26 26 0 0 0 19.83 12a26 26 0 0 0-.24-5zM10 15v-6l5 3-5 3z"/>
        </svg>
    </div>
    <div>
        <div class="yt-header-title">Las Damitas Histeria</div>
        <div class="yt-header-sub">Agente de análisis · Powered by Gemini</div>
    </div>
    <div class="yt-header-badge">
        <span class="dot"></span> Gemini conectado
    </div>
</div>
""", unsafe_allow_html=True)


# =========================
# BARRA DE FILTROS
# (va justo después del encabezado y antes del chat)
# =========================

st.markdown("""
<style>
.yt-filters-label {
    font-size: 13px;
    color: #888;
    font-weight: 500;
    margin-right: 10px;
    white-space: nowrap;
}
.yt-filters-row {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    padding: 10px 0 16px 0;
    border-bottom: 1px solid #efefef;
    margin-bottom: 16px;
}
.yt-filter-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 5px 13px;
    border-radius: 20px;
    border: 1px solid #e0e0e0;
    background: #fafafa;
    font-size: 12px;
    color: #333;
    cursor: pointer;
    transition: background 0.15s, border 0.15s;
    white-space: nowrap;
    font-family: 'Segoe UI', sans-serif;
}
.yt-filter-chip:hover {
    background: #f0f0f0;
    border-color: #ccc;
}
.yt-filter-chip.active {
    background: #0f0f0f;
    color: white;
    border-color: #0f0f0f;
}
</style>

<div class="yt-filters-row">
    <span class="yt-filters-label">Filtrar:</span>
    <span class="yt-filter-chip">📱 Shorts</span>
    <span class="yt-filter-chip">🎙️ Podcasts</span>
    <span class="yt-filter-chip">📅 2024</span>
    <span class="yt-filter-chip">📅 2023</span>
    <span class="yt-filter-chip">⚡ Videos cortos</span>
    <span class="yt-filter-chip">⏱️ Videos largos</span>
    <span class="yt-filter-chip">💬 Comentarios</span>
</div>
""", unsafe_allow_html=True)


# ── Filtros funcionales con st.pills ──────────────────────────────────────
# st.pills renderiza chips nativos de Streamlit que sí disparan eventos.
# Lo ponemos justo debajo del HTML visual para que el usuario lo use.



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
# 8. MEMORIA DE CONVERSACIÓN
# =========================
# Reemplaza tu bloque actual de "if messages not in session_state"

if "messages" not in st.session_state:
    st.session_state.messages = []


# =========================
# 9. MOSTRAR HISTORIAL
# =========================

# Pantalla de bienvenida: solo se muestra si no hay mensajes aún
if not st.session_state.messages:
    st.markdown("""
    <style>
    .yt-welcome {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 60px 20px 40px;
    }
    .yt-welcome-icon {
        width: 64px;
        height: 64px;
        background: #ff0000;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 14px rgba(255,0,0,0.25);
    }
    .yt-welcome-icon svg {
        width: 34px;
        height: 34px;
        fill: white;
    }
    .yt-welcome-title {
        font-size: 22px;
        font-weight: 700;
        color: #0f0f0f;
        margin-bottom: 12px;
        font-family: 'Segoe UI', sans-serif;
    }
    .yt-welcome-desc {
        font-size: 14px;
        color: #606060;
        max-width: 420px;
        line-height: 1.7;
        font-family: 'Segoe UI', sans-serif;
    }
    .yt-welcome-desc b {
        color: #0f0f0f;
        font-weight: 600;
    }
    </style>

    <div class="yt-welcome">
        <div class="yt-welcome-icon">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M19.59 7a2.5 2.5 0 0 0-1.76-1.76C16.46 5 12 5 12 5s-4.46 0-5.83.24A2.5 2.5 0 0 0 4.41 7 26 26 0 0 0 4.17 12a26 26 0 0 0 .24 5 2.5 2.5 0 0 0 1.76 1.76C7.54 19 12 19 12 19s4.46 0 5.83-.24A2.5 2.5 0 0 0 19.59 17 26 26 0 0 0 19.83 12a26 26 0 0 0-.24-5zM10 15v-6l5 3-5 3z"/>
            </svg>
        </div>
        <div class="yt-welcome-title">Hola, soy tu agente de YouTube</div>
        <div class="yt-welcome-desc">
            Puedo analizar el rendimiento de <b>Las Damitas Histeria</b>, encontrar en
            qué episodio hablaron de un tema, decirte los mejores días para
            publicar y mucho más. ¡Pregúntame lo que necesites!
        </div>
    </div>
    """, unsafe_allow_html=True)

# Mostrar historial de mensajes (cuando ya hay conversación)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# =========================
# 10. CAPTURAR PREGUNTA DEL USUARIO
# =========================
prompt = st.chat_input("Pregunta sobre el canal… ej: ¿De qué hablaron en el episodio 40?")

if "prompt_sugerido" in st.session_state:
    prompt = st.session_state.prompt_sugerido
    del st.session_state.prompt_sugerido

if prompt:

    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Consultando BigQuery y generando respuesta..."):
            try:
                respuesta_texto = agent.answer(f"{contexto_filtros} {prompt}".strip())
                st.markdown(respuesta_texto)
                st.session_state.messages.append({"role": "assistant", "content": respuesta_texto})

            except Exception as e:
                mensaje_error = (
                    "**Ocurrió un error al procesar tu pregunta:**\n\n"
                    f"`{str(e)}`\n\n"
                    "Revisa tus Secrets y permisos de BigQuery."
                )
                st.error(mensaje_error)
                st.session_state.messages.append({"role": "assistant", "content": mensaje_error})
