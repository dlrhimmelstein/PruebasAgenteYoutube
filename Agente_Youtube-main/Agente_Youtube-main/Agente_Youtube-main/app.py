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
# 4. ESTILOS VISUALES
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
  --bg-base:      #F0F0F0;
  --bg-surface:   #F7F7F7;
  --bg-card:      #FFFFFF;
  --bg-sidebar:   #EBEBEB;
  --border:       #E0E0E0;
  --border-dark:  #CCCCCC;
  --text-primary: #282828;
  --text-muted:   #999999;
  --yt-red:       #E8001C;
  --user-blue:    #1A56A8;
  --shadow-xs:    0 1px 3px rgba(40,40,40,0.06);
  --shadow-sm:    0 2px 8px rgba(40,40,40,0.08);
  --r-sm: 8px; --r-md: 12px; --r-lg: 18px;
}

html, body, [class*="css"] {
  font-family: 'DM Sans', 'Inter', system-ui, sans-serif !important;
  background-color: var(--bg-base) !important;
  color: var(--text-primary) !important;
  font-size: 14px;
}

/* ── Ocultar chrome de Streamlit ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Contenedor principal ── */
.block-container {
  padding-top: 0 !important;
  padding-bottom: 5rem !important;
  padding-left: 1rem !important;
  padding-right: 1rem !important;
  max-width: 100% !important;
}

/* ══════════════════════════════════
   HEADER
══════════════════════════════════ */
.yt-header {
  position: sticky;
  top: 0;
  z-index: 100;
  width: 100%;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 58px;
  box-shadow: var(--shadow-xs);
  box-sizing: border-box;
  margin-bottom: 0;
}

.yt-header .left  { display: flex; align-items: center; gap: 10px; }
.yt-header .right { display: flex; align-items: center; gap: 8px; }

.yt-icon-box {
  width: 34px; height: 24px;
  background: var(--yt-red);
  border-radius: 7px;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 1px 4px rgba(232,0,28,.25);
}
.yt-icon-box svg { width: 14px; height: 14px; fill: white; }

.hdr-name { font-size: 15px; font-weight: 600; color: var(--text-primary); letter-spacing: -.3px; line-height: 1.2; }
.hdr-sub  { font-size: 11px; color: var(--text-muted); font-weight: 400; }

.stat-pill {
  display: inline-flex; align-items: center; gap: 6px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 5px 13px;
  font-size: 12px; color: #555; font-weight: 400;
  white-space: nowrap;
}
.dot-green {
  width: 7px; height: 7px; border-radius: 50%;
  background: #2BA84A;
  animation: pulse 2.4s infinite;
  flex-shrink: 0;
}
@keyframes pulse {
  0%,100% { opacity:1; transform:scale(1); }
  50%      { opacity:.5; transform:scale(.85); }
}

.clear-btn {
  background: var(--bg-card);
  border: 1px solid var(--border-dark);
  border-radius: 8px;
  color: #555;
  font-size: 12px;
  padding: 5px 13px;
  cursor: pointer;
  font-family: inherit;
  transition: all .15s;
}
.clear-btn:hover { background: var(--bg-surface); color: var(--text-primary); }

.avatar {
  width: 34px; height: 34px; border-radius: 50%;
  background: var(--yt-red);
  color: white; font-size: 11px; font-weight: 600;
  display: flex; align-items: center; justify-content: center;
  letter-spacing: -.3px; flex-shrink: 0;
}

/* ══════════════════════════════════
   CHIPS BAR
══════════════════════════════════ */
.chips-bar {
  display: flex; align-items: center; gap: 7px;
  padding: 9px 4px;
  overflow-x: auto; scrollbar-width: none;
  border-bottom: 1px solid var(--border);
  background: var(--bg-surface);
  flex-wrap: nowrap;
}
.chips-bar::-webkit-scrollbar { display: none; }
.chips-label { font-size: 11.5px; color: var(--text-muted); font-weight: 500; white-space: nowrap; }

/* Los chips se renderizan como botones de Streamlit — los sobreescribimos */
.chips-bar .stButton > button {
  border-radius: 20px !important;
  border: 1px solid var(--border-dark) !important;
  background: var(--bg-card) !important;
  color: #555 !important;
  font-size: 12px !important;
  font-weight: 400 !important;
  padding: 4px 13px !important;
  box-shadow: var(--shadow-xs) !important;
  white-space: nowrap !important;
  height: auto !important;
  line-height: 1.4 !important;
}
.chips-bar .stButton > button:hover {
  background: var(--bg-base) !important;
  border-color: #BBBBBB !important;
  color: var(--text-primary) !important;
}

/* ══════════════════════════════════
   CHAT MESSAGES
══════════════════════════════════ */
[data-testid="stChatMessage"] {
  background: transparent !important;
  padding: 0 !important;
  margin-bottom: 14px !important;
}

/* Burbuja agente */
[data-testid="stChatMessage"][data-testid*="assistant"] [data-testid="stChatMessageContent"],
[data-testid="stChatMessage"]:not(:has([data-testid="stChatMessageAvatarUser"])) [data-testid="stChatMessageContent"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 4px var(--r-lg) var(--r-lg) var(--r-lg) !important;
  box-shadow: var(--shadow-sm) !important;
  color: var(--text-primary) !important;
  font-size: 13.5px !important;
  line-height: 1.62 !important;
}

/* Burbuja usuario */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
  background: var(--user-blue) !important;
  border: 1px solid var(--user-blue) !important;
  border-radius: var(--r-lg) 4px var(--r-lg) var(--r-lg) !important;
  color: white !important;
  font-size: 13.5px !important;
  line-height: 1.62 !important;
}

/* ══════════════════════════════════
   CHAT INPUT
══════════════════════════════════ */
[data-testid="stChatInput"] > div {
  background: var(--bg-card) !important;
  border: 1.5px solid var(--border-dark) !important;
  border-radius: 22px !important;
  box-shadow: var(--shadow-xs) !important;
}
[data-testid="stChatInput"] textarea {
  font-family: 'DM Sans', inherit !important;
  font-size: 14px !important;
  color: var(--text-primary) !important;
  background: transparent !important;
}
[data-testid="stChatInput"] button {
  background: var(--yt-red) !important;
  border-radius: 50% !important;
  box-shadow: 0 2px 6px rgba(232,0,28,.25) !important;
}
.stChatInputContainer > div { padding: 4px 6px 4px 14px !important; }

/* Footer hint */
.input-hint {
  text-align: center; font-size: 10.5px;
  color: var(--text-muted); margin-top: 5px;
}

/* ══════════════════════════════════
   SIDEBAR
══════════════════════════════════ */
[data-testid="stSidebar"] {
  background-color: var(--bg-sidebar) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }

/* Sección label */
.sb-label {
  font-size: 10.5px; font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase; letter-spacing: .9px;
  padding: 0 6px; margin: 12px 0 6px;
}

/* Item con ícono */
.sb-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 8px 8px; border-radius: var(--r-sm);
  cursor: default; margin-bottom: 2px;
  transition: background .15s;
}
.sb-item:hover { background: rgba(40,40,40,.06); }

.sb-icon-box {
  width: 32px; height: 32px; border-radius: 7px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; flex-shrink: 0;
  box-shadow: var(--shadow-xs);
}

.sb-item-title { font-size: 12.5px; font-weight: 500; color: var(--text-primary); line-height: 1.3; }
.sb-item-sub   { font-size: 11px;   color: var(--text-muted); margin-top: 1px; }

.sb-divider { height: 1px; background: var(--border); margin: 6px 0; }

/* Stats al fondo */
.sb-stats {
  border-top: 1px solid var(--border);
  padding: 12px 6px 16px;
  background: var(--bg-surface);
  margin-top: auto;
}
.sb-stat-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 5px 0; font-size: 12px;
}
.sb-stat-lbl { color: var(--text-muted); }
.sb-stat-val { color: var(--text-primary); font-weight: 500; }
.sb-stat-val.red { color: var(--yt-red); }

/* ══════════════════════════════════
   BOTONES SIDEBAR (accesos rápidos)
══════════════════════════════════ */
.stButton > button {
  border-radius: 20px !important;
  border: 1px solid var(--border-dark) !important;
  background: var(--bg-card) !important;
  color: #555 !important;
  font-family: 'DM Sans', inherit !important;
  font-size: 12px !important;
  font-weight: 400 !important;
  padding: 5px 13px !important;
  box-shadow: var(--shadow-xs) !important;
  transition: all .15s !important;
}
.stButton > button:hover {
  background: var(--bg-base) !important;
  border-color: #BBBBBB !important;
  color: var(--text-primary) !important;
}
</style>
""", unsafe_allow_html=True)


# =========================
# 5. HEADER
# =========================
st.markdown("""
<div class="yt-header">
  <div class="left">
    <div class="yt-icon-box">
      <svg viewBox="0 0 24 24"><path d="M21.543 6.498C22 8.28 22 12 22 12s0 3.72-.457 5.502c-.254.985-.997 1.76-1.938 2.022C17.896 20 12 20 12 20s-5.896 0-7.605-.476c-.945-.266-1.687-1.04-1.938-2.022C2 15.72 2 12 2 12s0-3.72.457-5.502c.254-.985.997-1.76 1.938-2.022C6.104 4 12 4 12 4s5.896 0 7.605.476c.945.266 1.687 1.04 1.938 2.022zM10 15.5l6-3.5-6-3.5v7z"/></svg>
    </div>
    <div>
      <div class="hdr-name">Las Damitas Histeria</div>
      <div class="hdr-sub">Agente de análisis · Powered by Gemini</div>
    </div>
  </div>
  <div class="right">
    <span class="stat-pill"><span class="dot-green"></span>Gemini conectado</span>
    <span class="stat-pill">🗓 299 videos</span>
    <button class="clear-btn" onclick="window.location.reload()">Limpiar chat</button>
    <div class="avatar">LDH</div>
  </div>
</div>
""", unsafe_allow_html=True)


# =========================
# 6. SIDEBAR
# =========================
with st.sidebar:

    # Logo sidebar
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;padding:14px 8px 12px;border-bottom:1px solid var(--border);margin-bottom:4px">
      <div class="yt-icon-box" style="width:34px;height:24px">
        <svg viewBox="0 0 24 24"><path d="M21.543 6.498C22 8.28 22 12 22 12s0 3.72-.457 5.502c-.254.985-.997 1.76-1.938 2.022C17.896 20 12 20 12 20s-5.896 0-7.605-.476c-.945-.266-1.687-1.04-1.938-2.022C2 15.72 2 12 2 12s0-3.72.457-5.502c.254-.985.997-1.76 1.938-2.022C6.104 4 12 4 12 4s5.896 0 7.605.476c.945.266 1.687 1.04 1.938 2.022zM10 15.5l6-3.5-6-3.5v7z" fill="white"/></svg>
      </div>
      <div>
        <div style="font-size:14px;font-weight:600;color:var(--text-primary);line-height:1.2">Las Damitas Histeria</div>
        <div style="font-size:11px;color:var(--text-muted)">Agente YouTube Analytics</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Accesos rápidos ──
    st.markdown('<div class="sb-label">Accesos rápidos</div>', unsafe_allow_html=True)

    quick_items = [
        ("🏆", "Top videos",              "Ranking por vistas",      "¿Cuáles son mis 5 videos con más vistas?"),
        ("📅", "Mejor día para publicar", "Análisis de rendimiento",  "¿Qué días de la semana son mejores para publicar?"),
        ("🎯", "Temas más exitosos",      "Por engagement",           "¿De qué temas habla más el canal y cuáles tienen más engagement?"),
        ("📈", "Resumen del canal",        "Stats generales",          "Dame un resumen general del canal con sus estadísticas principales."),
        ("🎬", "Formatos que funcionan",  "Shorts vs podcasts",       "¿Qué formato de video funciona mejor en el canal?"),
        ("❤️", "Mayor engagement",        "Likes y comentarios",      "¿Cuáles son mis videos con mayor engagement rate?"),
    ]

    for icon, title, sub, question in quick_items:
        st.markdown(f"""
        <div class="sb-item">
          <div class="sb-icon-box">{icon}</div>
          <div>
            <div class="sb-item-title">{title}</div>
            <div class="sb-item-sub">{sub}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        # Botón invisible superpuesto al item (workaround Streamlit)
        if st.button(f"↗ {title}", key=f"q_{title}", use_container_width=True):
            st.session_state["pending_q"] = question

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)

    # ── Buscar video ──
    st.markdown('<div class="sb-label">Buscar video</div>', unsafe_allow_html=True)

    search_items = [
        ("🔍", "Buscar por tema",  '"¿En qué ep hablaron de X?"', "¿En qué episodio hablaron de "),
        ("🎥", "Analizar video",    "Por título o URL",             "Analiza el video: "),
    ]
    for icon, title, sub, prefix in search_items:
        st.markdown(f"""
        <div class="sb-item">
          <div class="sb-icon-box">{icon}</div>
          <div>
            <div class="sb-item-title">{title}</div>
            <div class="sb-item-sub">{sub}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"↗ {title}", key=f"s_{title}", use_container_width=True):
            st.session_state["pending_q"] = prefix

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)

    # ── Probar conexión ──
    if st.button("🔌 Probar BigQuery", use_container_width=True):
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

    if st.button("🗑️ Limpiar conversación", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    # ── Canal al día (stats fijas) ──
    st.markdown("""
    <div class="sb-stats">
      <div class="sb-label" style="margin-top:0">Canal al día</div>
      <div class="sb-stat-row"><span class="sb-stat-lbl">Videos</span>       <span class="sb-stat-val">299</span></div>
      <div class="sb-stat-row"><span class="sb-stat-lbl">Views totales</span> <span class="sb-stat-val">16.7M</span></div>
      <div class="sb-stat-row"><span class="sb-stat-lbl">Likes totales</span> <span class="sb-stat-val">716K</span></div>
      <div class="sb-stat-row"><span class="sb-stat-lbl">Comentarios</span>   <span class="sb-stat-val">34.8K</span></div>
      <div class="sb-stat-row"><span class="sb-stat-lbl">Estado del agente</span><span class="sb-stat-val red">● Activo</span></div>
    </div>
    """, unsafe_allow_html=True)


# =========================
# 7. CHIPS / FILTROS RÁPIDOS
# =========================
chips = [
    ("📱 Shorts",       "Muéstrame solo los Shorts del canal ordenados por vistas."),
    ("🎙️ Podcasts",     "Muéstrame los episodios de podcast ordenados por vistas."),
    ("📅 2024",         "¿Cuáles son los mejores videos del 2024?"),
    ("📅 2023",         "¿Cuáles son los mejores videos del 2023?"),
    ("⚡ Videos cortos", "Muéstrame los videos más cortos ordenados por engagement."),
    ("⏳ Videos largos", "Muéstrame los videos más largos con más views."),
    ("💬 Comentarios",  "¿Qué videos tienen más comentarios?"),
]

st.markdown('<div class="chips-bar">', unsafe_allow_html=True)
st.markdown('<span class="chips-label">Filtrar:</span>', unsafe_allow_html=True)
chip_cols = st.columns(len(chips))
for idx, (label, question) in enumerate(chips):
    with chip_cols[idx]:
        if st.button(label, key=f"chip_{idx}"):
            st.session_state["pending_q"] = question
st.markdown('</div>', unsafe_allow_html=True)


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
# 10. PREGUNTA PENDIENTE (chips / sidebar)
# =========================
pending = st.session_state.pop("pending_q", None)


# =========================
# 11. CAPTURAR PREGUNTA DEL USUARIO
# =========================
prompt = st.chat_input("Pregunta sobre el canal… ej: ¿De qué hablaron en el episodio 40?")

active_prompt = pending or prompt

if active_prompt:
    st.chat_message("user").markdown(active_prompt)
    st.session_state.messages.append({"role": "user", "content": active_prompt})

    with st.chat_message("assistant"):
        with st.spinner("Consultando BigQuery y generando respuesta..."):
            try:
                respuesta_texto = agent.answer(active_prompt)
                st.markdown(respuesta_texto)
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

# Hint debajo del input
st.markdown(
    '<div class="input-hint">El agente consulta BigQuery en tiempo real · Respuestas basadas en datos reales</div>',
    unsafe_allow_html=True
)
