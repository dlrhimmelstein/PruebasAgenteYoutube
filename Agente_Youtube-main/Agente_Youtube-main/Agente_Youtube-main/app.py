# -*- coding: utf-8 -*-

import os
import streamlit as st

# =========================
# 1. CONFIGURACIÓN DE PÁGINA
# =========================
st.set_page_config(
    page_title="Las Damitas Histeria | Agente YouTube",
    page_icon="▶️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# 2. CARGA SEGURA DE CREDENCIALES
# =========================
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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
try:
    from agent import agent, retriever
except Exception as e:
    st.error("🚨 Error al importar el agente desde agent.py.")
    st.exception(e)
    st.stop()

# =========================
# 4. ESTILOS VISUALES (diseño del HTML integrado)
# =========================
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

  :root {
    --bg-base:       #F0F0F0;
    --bg-surface:    #F7F7F7;
    --bg-card:       #FFFFFF;
    --bg-sidebar:    #EBEBEB;
    --bg-header:     #FFFFFF;
    --border:        #E0E0E0;
    --border-dark:   #CCCCCC;
    --text-primary:  #282828;
    --text-secondary:#666666;
    --text-muted:    #999999;
    --yt-red:        #E8001C;
    --yt-red-soft:   #FFF0F0;
    --yt-red-mid:    #FFDDDD;
    --user-bubble:   #1A56A8;
    --font-main:     'DM Sans', system-ui, sans-serif;
    --radius-sm:     8px;
    --radius-md:     12px;
    --radius-lg:     18px;
    --shadow-xs:     0 1px 3px rgba(40,40,40,0.06);
    --shadow-sm:     0 2px 8px rgba(40,40,40,0.08);
    --shadow-md:     0 4px 16px rgba(40,40,40,0.10);
  }

  html, body, [class*="css"] {
    font-family: var(--font-main) !important;
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
  }

  /* ── Ocultar elementos Streamlit ── */
  #MainMenu { visibility: hidden; }
  footer    { visibility: hidden; }
  header    { visibility: hidden; }

  /* ── Contenedor principal ── */
  .block-container {
    padding-top: 0 !important;
    padding-bottom: 6rem;
    padding-left: 1.5rem;
    padding-right: 1.5rem;
    max-width: 100% !important;
  }

  /* ── Header ── */
  .yt-header {
    width: 100%;
    background: var(--bg-header);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 20px;
    height: 58px;
    box-shadow: var(--shadow-xs);
    margin-bottom: 1.2rem;
    box-sizing: border-box;
  }

  .yt-header .logo-area {
    display: flex;
    align-items: center;
    gap: 11px;
  }

  .yt-icon {
    width: 34px;
    height: 24px;
    background: var(--yt-red);
    border-radius: 7px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 1px 4px rgba(232,0,28,0.25);
    color: white;
    font-size: 13px;
    font-weight: 800;
  }

  .channel-name {
    font-size: 15px;
    font-weight: 600;
    color: var(--text-primary);
    letter-spacing: -0.3px;
    line-height: 1.2;
  }

  .channel-sub {
    font-size: 11px;
    color: var(--text-muted);
    font-weight: 400;
  }

  .stat-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 5px 13px;
    font-size: 12px;
    color: var(--text-secondary);
    font-weight: 400;
    margin-left: 8px;
  }

  .dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #2BA84A;
    display: inline-block;
    animation: pulse 2.4s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.5; transform: scale(0.85); }
  }

  /* ── Info box ── */
  .info-box {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 12px 16px;
    font-size: 13px;
    color: var(--text-secondary);
    box-shadow: var(--shadow-xs);
    margin-bottom: 1rem;
  }

  .info-box b { color: var(--text-primary); }

  /* ── Chips bar ── */
  .chips-bar {
    display: flex;
    align-items: center;
    gap: 7px;
    padding: 9px 0;
    overflow-x: auto;
    scrollbar-width: none;
    flex-wrap: wrap;
    margin-bottom: 0.75rem;
  }

  .chip-label {
    font-size: 11.5px;
    color: var(--text-muted);
    font-weight: 500;
    white-space: nowrap;
  }

  /* ── Chat messages ── */
  [data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    margin-bottom: 0.75rem;
  }

  [data-testid="stChatMessageContent"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px var(--radius-lg) var(--radius-lg) var(--radius-lg) !important;
    box-shadow: var(--shadow-sm) !important;
    padding: 10px 14px !important;
    font-size: 13.5px !important;
    color: var(--text-primary) !important;
    line-height: 1.62 !important;
  }

  /* Burbuja usuario */
  [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
    background: var(--user-bubble) !important;
    color: white !important;
    border-color: var(--user-bubble) !important;
    border-radius: var(--radius-lg) 4px var(--radius-lg) var(--radius-lg) !important;
  }

  /* ── Chat input ── */
  .stChatInput > div {
    background: var(--bg-card) !important;
    border: 1.5px solid var(--border-dark) !important;
    border-radius: 22px !important;
    box-shadow: var(--shadow-xs) !important;
    padding: 4px 8px 4px 16px !important;
  }

  .stChatInput textarea {
    font-family: var(--font-main) !important;
    font-size: 14px !important;
    color: var(--text-primary) !important;
    background: transparent !important;
  }

  .stChatInput button {
    background: var(--yt-red) !important;
    border-radius: 50% !important;
    border: none !important;
    box-shadow: 0 2px 6px rgba(232,0,28,0.2) !important;
  }

  /* ── Botones Streamlit ── */
  .stButton > button {
    border-radius: 20px !important;
    border: 1px solid var(--border-dark) !important;
    background: var(--bg-card) !important;
    color: var(--text-secondary) !important;
    font-family: var(--font-main) !important;
    font-size: 12px !important;
    font-weight: 400 !important;
    padding: 5px 13px !important;
    box-shadow: var(--shadow-xs) !important;
    transition: all 0.15s !important;
  }

  .stButton > button:hover {
    background: var(--bg-base) !important;
    border-color: #BBBBBB !important;
    color: var(--text-primary) !important;
  }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border) !important;
  }

  [data-testid="stSidebar"] > div:first-child {
    padding-top: 1rem;
  }

  .sidebar-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 6px 14px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 12px;
  }

  .sb-icon {
    width: 34px;
    height: 24px;
    background: var(--yt-red);
    border-radius: 7px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 12px;
    font-weight: 800;
    flex-shrink: 0;
  }

  .sb-title { font-size: 14px; font-weight: 600; color: var(--text-primary); line-height: 1.2; }
  .sb-sub   { font-size: 11px; color: var(--text-muted); }

  .sidebar-label {
    font-size: 10.5px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.9px;
    margin: 12px 0 6px 6px;
  }

  .sidebar-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 8px 8px;
    border-radius: var(--radius-sm);
    font-size: 13px;
    cursor: default;
    margin-bottom: 2px;
  }

  .sidebar-item:hover { background: rgba(40,40,40,0.06); }

  .qb-icon {
    width: 32px;
    height: 32px;
    border-radius: 7px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    flex-shrink: 0;
    box-shadow: var(--shadow-xs);
  }

  .qb-label { font-size: 12.5px; font-weight: 500; color: var(--text-primary); }
  .qb-sub   { font-size: 11px; color: var(--text-muted); margin-top: 1px; }

  .sidebar-divider {
    height: 1px;
    background: var(--border);
    margin: 8px 0;
  }

  .data-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 10px 12px;
    font-size: 12px;
    color: var(--text-primary);
    box-shadow: var(--shadow-xs);
    margin: 6px 0;
  }

  .data-card b { color: var(--text-muted); font-size: 10.5px; display: block; margin-bottom: 2px; }
  .data-card span {
    font-family: 'DM Mono', monospace;
    background: var(--bg-surface);
    padding: 2px 6px;
    border-radius: 5px;
    color: #059669;
    font-size: 11px;
  }

  .sidebar-stats {
    border-top: 1px solid var(--border);
    padding: 12px 6px;
    margin-top: 8px;
  }

  .mini-stat {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 4px 0;
    font-size: 12px;
  }

  .ms-label { color: var(--text-muted); }
  .ms-val   { color: var(--text-primary); font-weight: 500; }
  .ms-val.red { color: var(--yt-red); }

  /* ── Video card en respuestas ── */
  .video-card {
    display: flex;
    gap: 10px;
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 10px;
    margin-top: 8px;
    text-decoration: none;
    color: inherit;
    box-shadow: var(--shadow-xs);
    transition: all 0.15s;
  }

  .video-card:hover {
    border-color: var(--border-dark);
    background: var(--bg-card);
    box-shadow: var(--shadow-sm);
  }

  .vc-thumb {
    width: 100px;
    height: 56px;
    background: var(--border);
    border-radius: 5px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-size: 18px;
    overflow: hidden;
  }

  .vc-thumb img { width: 100%; height: 100%; object-fit: cover; border-radius: 5px; }
  .vc-title { font-size: 12.5px; font-weight: 500; line-height: 1.4; }
  .vc-tag   { font-size: 10.5px; color: var(--text-muted); }
  .vc-tag.green { color: #2BA84A; font-weight: 500; }
  .vc-tag.red   { color: var(--yt-red); }

  .metric-row { display: flex; gap: 10px; margin-top: 8px; flex-wrap: wrap; }

  .metric {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 7px 11px;
    text-align: center;
    min-width: 76px;
  }

  .metric .m-val   { font-size: 15px; font-weight: 600; color: var(--text-primary); }
  .metric .m-label { font-size: 9.5px; color: var(--text-muted); margin-top: 2px; text-transform: uppercase; letter-spacing: 0.4px; }

  /* ── Spinner ── */
  [data-testid="stSpinner"] { color: var(--yt-red) !important; }
</style>
""", unsafe_allow_html=True)

# =========================
# 5. ENCABEZADO
# =========================
st.markdown("""
<div class="yt-header">
  <div class="logo-area">
    <div class="yt-icon">▶</div>
    <div>
      <div class="channel-name">Las Damitas Histeria</div>
      <div class="channel-sub">Agente de análisis · Powered by Gemini</div>
    </div>
  </div>
  <div>
    <span class="stat-pill"><span class="dot"></span> Gemini conectado</span>
    <span class="stat-pill">📊 299 videos</span>
  </div>
</div>
""", unsafe_allow_html=True)

# =========================
# 6. SIDEBAR
# =========================
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
      <div class="sb-icon">▶</div>
      <div>
        <div class="sb-title">Las Damitas Histeria</div>
        <div class="sb-sub">Agente YouTube Analytics</div>
      </div>
    </div>

    <div class="sidebar-label">Accesos rápidos</div>
    """, unsafe_allow_html=True)

    # Quick access buttons (functional)
    quick_questions = [
        ("🏆", "Top videos",              "Ranking por vistas",      "¿Cuáles son mis 5 videos con más vistas?"),
        ("📅", "Mejor día para publicar", "Análisis de rendimiento",  "¿Qué días de la semana son mejores para publicar?"),
        ("🎯", "Temas más exitosos",      "Por engagement",           "¿De qué temas habla más el canal y cuáles tienen más engagement?"),
        ("📈", "Resumen del canal",        "Stats generales",          "Dame un resumen general del canal con sus estadísticas principales."),
        ("🎬", "Formatos que funcionan",  "Shorts vs podcasts",       "¿Qué formato de video funciona mejor en el canal?"),
        ("❤️", "Mayor engagement",        "Likes y comentarios",      "¿Cuáles son mis videos con mayor engagement rate?"),
    ]

    for icon, label, sublabel, question in quick_questions:
        col1, col2 = st.columns([0.15, 0.85])
        with col1:
            st.markdown(f'<div class="qb-icon">{icon}</div>', unsafe_allow_html=True)
        with col2:
            if st.button(label, key=f"quick_{label}", help=sublabel, use_container_width=True):
                st.session_state["pending_question"] = question

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="sidebar-label">Buscar video</div>
    """, unsafe_allow_html=True)

    if st.button("🔍  Buscar por tema", use_container_width=True):
        st.session_state["pending_question"] = "¿En qué episodio hablaron de "

    if st.button("🎥  Analizar video", use_container_width=True):
        st.session_state["pending_question"] = "Analiza el video: "

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="sidebar-label">Fuente de datos</div>
    <div class="data-card">
      <div><b>Proyecto</b><span>mineria-datos-493000</span></div>
      <div style="margin-top:6px"><b>Dataset</b><span>youtube</span></div>
      <div style="margin-top:6px"><b>Tabla</b><span>fact_final</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-label">Probar conexión</div>', unsafe_allow_html=True)
    if st.button("Probar BigQuery", use_container_width=True):
        with st.spinner("Verificando conexión con BigQuery..."):
            try:
                info = retriever.test_connection()
                st.success("✅ Conexión exitosa")
                st.write("**Tabla:**", info["tabla"])
                st.write("**Filas:**", info["filas"])
                st.write("**Columnas:**", info["columnas"])
            except Exception as e:
                st.error("❌ No se pudo conectar con BigQuery.")
                st.exception(e)

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    if st.button("🗑️  Limpiar conversación", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    # Stats panel
    st.markdown("""
    <div class="sidebar-stats">
      <div class="sidebar-label">Canal al día</div>
      <div class="mini-stat"><span class="ms-label">Videos</span><span class="ms-val">299</span></div>
      <div class="mini-stat"><span class="ms-label">Views totales</span><span class="ms-val">16.7M</span></div>
      <div class="mini-stat"><span class="ms-label">Likes totales</span><span class="ms-val">716K</span></div>
      <div class="mini-stat"><span class="ms-label">Comentarios</span><span class="ms-val">34.8K</span></div>
      <div class="mini-stat"><span class="ms-label">Estado del agente</span><span class="ms-val red">● Activo</span></div>
    </div>
    """, unsafe_allow_html=True)

# =========================
# 7. CHIPS / FILTROS RÁPIDOS
# =========================
st.markdown("""
<div class="info-box">
  <b>¿Qué puede hacer este agente?</b><br>
  Puede responder sobre videos, métricas, temas, transcripciones, ranking de contenido,
  recomendaciones y predicciones de rendimiento del canal.
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="chips-bar"><span class="chip-label">Filtrar:</span>', unsafe_allow_html=True)
chip_cols = st.columns(7)
chips = [
    ("📱 Shorts",        "Muéstrame solo los Shorts del canal ordenados por vistas."),
    ("🎙️ Podcasts",      "Muéstrame los episodios de podcast ordenados por vistas."),
    ("📅 2024",          "¿Cuáles son los mejores videos del 2024?"),
    ("📅 2023",          "¿Cuáles son los mejores videos del 2023?"),
    ("⚡ Cortos",         "Muéstrame los videos más cortos ordenados por engagement."),
    ("⏳ Largos",         "Muéstrame los videos más largos con más views."),
    ("💬 Comentarios",   "¿Qué videos tienen más comentarios?"),
]
for idx, (label, question) in enumerate(chips):
    with chip_cols[idx]:
        if st.button(label, key=f"chip_{idx}", use_container_width=True):
            st.session_state["pending_question"] = question
st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 8. MEMORIA DE CONVERSACIÓN
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hola 👋 Soy tu agente de análisis de YouTube para **Las Damitas Histeria**. "
                "Puedo analizar el rendimiento del canal, encontrar en qué episodio hablaron de "
                "un tema, decirte los mejores días para publicar y mucho más. "
                "¡Pregúntame lo que necesites!"
            )
        }
    ]

# =========================
# 9. MOSTRAR HISTORIAL
# =========================
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# =========================
# 10. MANEJAR PREGUNTA RÁPIDA (sidebar / chips)
# =========================
pending = st.session_state.pop("pending_question", None)

# =========================
# 11. CAPTURAR PREGUNTA DEL USUARIO
# =========================
prompt = st.chat_input(
    "Pregunta sobre el canal… ej: ¿De qué hablaron en el episodio 40?"
)

# Usar pregunta pendiente o del input
active_prompt = pending or prompt

if active_prompt:
    st.chat_message("user").markdown(active_prompt)
    st.session_state.messages.append({"role": "user", "content": active_prompt})

    with st.chat_message("assistant"):
        with st.spinner("Consultando BigQuery y generando respuesta…"):
            try:
                respuesta_texto = agent.answer(active_prompt)
                st.markdown(respuesta_texto, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": respuesta_texto})
            except Exception as e:
                mensaje_error = (
                    "**Ocurrió un error al procesar tu pregunta:**\n\n"
                    f"`{str(e)}`\n\n"
                    "Revisa que tus Secrets estén configurados correctamente "
                    "y que la cuenta de servicio tenga permisos para BigQuery."
                )
                st.error(mensaje_error)
                st.exception(e)
                st.session_state.messages.append({"role": "assistant", "content": mensaje_error})

    if pending:
        st.rerun()
