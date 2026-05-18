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


<!-- ===================== SIDEBAR ===================== -->
<style>
  .yt-sidebar {
    width: 220px;
    min-height: 100vh;
    background: #fff;
    border-right: 1px solid #e5e5e5;
    display: flex;
    flex-direction: column;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
    color: #111;
    box-sizing: border-box;
  }
  .yt-sidebar-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 16px 16px 12px;
    border-bottom: 1px solid #f0f0f0;
  }
  .yt-logo-circle {
    width: 34px;
    height: 34px;
    background: #ff0000;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  .yt-logo-circle svg {
    width: 18px;
    height: 18px;
    fill: white;
  }
  .yt-header-title { font-size: 13px; font-weight: 600; color: #111; line-height: 1.3; }
  .yt-header-sub   { font-size: 11px; color: #888; line-height: 1.3; }
 
  .yt-section-label {
    padding: 12px 16px 4px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: #aaa;
    text-transform: uppercase;
  }
 
  .yt-menu-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 8px 16px;
    cursor: pointer;
    transition: background 0.12s;
    text-decoration: none;
    color: inherit;
  }
  .yt-menu-item:hover { background: #f5f5f5; }
 
  .yt-icon-box {
    width: 30px;
    height: 30px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-size: 15px;
  }
  .icon-orange { background: #fff3e0; color: #e65c00; }
  .icon-blue   { background: #e3f2fd; color: #1565c0; }
  .icon-green  { background: #e8f5e9; color: #2e7d32; }
  .icon-purple { background: #f3e5f5; color: #6a1b9a; }
  .icon-pink   { background: #fce4ec; color: #880e4f; }
  .icon-teal   { background: #e0f2f1; color: #00695c; }
  .icon-yellow { background: #fffde7; color: #f57f17; }
 
  .yt-item-title { font-size: 13px; font-weight: 500; color: #111; line-height: 1.3; }
  .yt-item-sub   { font-size: 11px; color: #888; line-height: 1.3; }
 
  .yt-divider { height: 1px; background: #f0f0f0; margin: 6px 0; }
 
  .yt-stats-box {
    margin: 0 12px 12px;
    background: #f9f9f9;
    border-radius: 10px;
    padding: 12px 14px;
    border: 1px solid #efefef;
  }
  .yt-stats-title {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: #aaa;
    text-transform: uppercase;
    margin-bottom: 8px;
  }
  .yt-stat-row {
    display: flex;
    justify-content: space-between;
    padding: 3px 0;
    font-size: 12px;
  }
  .yt-stat-label { color: #777; }
  .yt-stat-val   { font-weight: 600; color: #111; }
  .yt-status-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 4px 0;
  }
  .yt-status-dot {
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #22c55e;
    margin-right: 5px;
  }
  .yt-status-label { font-size: 12px; color: #777; }
  .yt-status-val   { font-size: 12px; font-weight: 600; color: #22c55e; }
</style>
 
<!-- Carga de íconos Tabler (puedes quitarla si ya la tienes en tu proyecto) -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
 
<div class="yt-sidebar">
 
  <!-- HEADER -->
  <div class="yt-sidebar-header">
    <div class="yt-logo-circle">
      <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M19.59 7a2.5 2.5 0 0 0-1.76-1.76C16.46 5 12 5 12 5s-4.46 0-5.83.24A2.5 2.5 0 0 0 4.41 7 26 26 0 0 0 4.17 12a26 26 0 0 0 .24 5 2.5 2.5 0 0 0 1.76 1.76C7.54 19 12 19 12 19s4.46 0 5.83-.24A2.5 2.5 0 0 0 19.59 17 26 26 0 0 0 19.83 12a26 26 0 0 0-.24-5zM10 15v-6l5 3-5 3z"/>
      </svg>
    </div>
    <div>
      <div class="yt-header-title">Las Damitas Histeria</div>
      <div class="yt-header-sub">Agente de análisis · Powered by Gemini</div>
    </div>
  </div>
 
  <!-- SECCIÓN: ACCESOS RÁPIDOS -->
  <div class="yt-section-label">Accesos rápidos</div>
 
  <div class="yt-menu-item">
    <div class="yt-icon-box icon-orange"><i class="ti ti-trophy" aria-hidden="true"></i></div>
    <div>
      <div class="yt-item-title">Top videos</div>
      <div class="yt-item-sub">Ranking por vistas</div>
    </div>
  </div>
 
  <div class="yt-menu-item">
    <div class="yt-icon-box icon-blue"><i class="ti ti-calendar-stats" aria-hidden="true"></i></div>
    <div>
      <div class="yt-item-title">Mejor día para publicar</div>
      <div class="yt-item-sub">Análisis de rendimiento</div>
    </div>
  </div>
 
  <div class="yt-menu-item">
    <div class="yt-icon-box icon-green"><i class="ti ti-flame" aria-hidden="true"></i></div>
    <div>
      <div class="yt-item-title">Temas más exitosos</div>
      <div class="yt-item-sub">Por engagement</div>
    </div>
  </div>
 
  <div class="yt-menu-item">
    <div class="yt-icon-box icon-purple"><i class="ti ti-chart-bar" aria-hidden="true"></i></div>
    <div>
      <div class="yt-item-title">Resumen del canal</div>
      <div class="yt-item-sub">Stats generales</div>
    </div>
  </div>
 
  <div class="yt-menu-item">
    <div class="yt-icon-box icon-teal"><i class="ti ti-layout-grid" aria-hidden="true"></i></div>
    <div>
      <div class="yt-item-title">Formatos que funcionan</div>
      <div class="yt-item-sub">Shorts vs podcasts</div>
    </div>
  </div>
 
  <div class="yt-menu-item">
    <div class="yt-icon-box icon-pink"><i class="ti ti-heart" aria-hidden="true"></i></div>
    <div>
      <div class="yt-item-title">Mayor engagement</div>
      <div class="yt-item-sub">Likes y comentarios</div>
    </div>
  </div>
 
  <div class="yt-divider"></div>
 
  <!-- SECCIÓN: BUSCAR VIDEO -->
  <div class="yt-section-label">Buscar video</div>
 
  <div class="yt-menu-item">
    <div class="yt-icon-box icon-blue"><i class="ti ti-search" aria-hidden="true"></i></div>
    <div>
      <div class="yt-item-title">Buscar por tema</div>
      <div class="yt-item-sub">¿En qué ep hablaron de X?</div>
    </div>
  </div>
 
  <div class="yt-menu-item">
    <div class="yt-icon-box icon-yellow"><i class="ti ti-video" aria-hidden="true"></i></div>
    <div>
      <div class="yt-item-title">Analizar video</div>
      <div class="yt-item-sub">Por título o URL</div>
    </div>
  </div>
 
  <!-- ESPACIADOR -->
  <div style="flex: 1;"></div>
 
  <!-- STATS AL FONDO -->
  <div class="yt-stats-box">
    <div class="yt-stats-title">Canal al día</div>
    <div class="yt-stat-row">
      <span class="yt-stat-label">Videos</span>
      <span class="yt-stat-val">299</span>
    </div>
    <div class="yt-stat-row">
      <span class="yt-stat-label">Views totales</span>
      <span class="yt-stat-val">16.7M</span>
    </div>
    <div class="yt-stat-row">
      <span class="yt-stat-label">Likes totales</span>
      <span class="yt-stat-val">716K</span>
    </div>
    <div class="yt-stat-row">
      <span class="yt-stat-label">Comentarios</span>
      <span class="yt-stat-val">34.8K</span>
    </div>
    <div class="yt-divider" style="margin: 6px 0;"></div>
    <div class="yt-status-row">
      <span class="yt-status-label">
        <span class="yt-status-dot"></span>Estado del agente
      </span>
      <span class="yt-status-val">Activo</span>
    </div>
  </div>
 
</div>
<!-- =================== FIN SIDEBAR =================== -->


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
