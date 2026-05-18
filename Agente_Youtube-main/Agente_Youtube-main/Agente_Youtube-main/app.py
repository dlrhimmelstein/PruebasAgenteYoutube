# -*- coding: utf-8 -*-

import os
import streamlit as st


# =========================
# 1. CONFIGURACIÓN DE PÁGINA
# =========================
# Debe ser el primer comando de Streamlit.
st.set_page_config(
    page_title="Las Damitas Histeria | Agente YouTube",
    page_icon="▶️",
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

st.markdown(
    """
    <style>

    /* =========================
       FONDO GENERAL
    ========================= */

    .stApp {
        background-color: #f7f7f7;
        color: #0f0f0f;
    }

    /* =========================
       CONTENEDOR PRINCIPAL
    ========================= */

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 6rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
    }

    /* =========================
       TIPOGRAFÍA
    ========================= */

    html, body, [class*="css"] {
        font-family: "Inter", "Segoe UI", sans-serif;
    }

    /* =========================
       HEADER TIPO YOUTUBE
    ========================= */

    .yt-header-wrapper {
        width: 100%;
        height: 60px;

        background: #ffffff;
        border-bottom: 1px solid #e5e5e5;

        display: flex;
        align-items: center;
        justify-content: space-between;

        padding: 0 1.2rem;

        margin:
            -1.2rem
            -2rem
            1.5rem
            -2rem;

        box-sizing: border-box;
    }

    .yt-logo {
        width: 34px;
        height: 34px;

        border-radius: 10px;

        background: #ff0000;
        color: white;

        display: flex;
        align-items: center;
        justify-content: center;

        font-size: 0.9rem;
        font-weight: 800;
    }

    .yt-title {
        color: #0f0f0f;
        font-size: 1rem;
        font-weight: 800;
        line-height: 1.1;
    }

    .yt-subtitle {
        color: #6b7280;
        font-size: 0.72rem;
        margin-top: 2px;
    }

    .yt-pill {
        background: #ffffff;

        border: 1px solid #e5e7eb;

        border-radius: 999px;

        padding:
            0.35rem
            0.8rem;

        font-size: 0.76rem;
        font-weight: 500;

        color: #4b5563;

        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }

    /* =========================
       CAJAS
    ========================= */

    .info-box {
        background-color: #ffffff;

        padding: 1rem 1.2rem;

        border-radius: 18px;

        border: 1px solid #e5e7eb;

        box-shadow: 0 2px 10px rgba(0,0,0,0.06);

        margin-bottom: 1.2rem;

        color: #374151;
    }

    .small-text {
        color: #6b7280;
        font-size: 0.85rem;
    }

    /* =========================
       BOTONES
    ========================= */

    .stButton > button {
        border-radius: 999px;

        border: 1px solid #d1d5db;

        background-color: #ffffff;

        color: #374151;

        font-weight: 600;

        padding:
            0.45rem
            0.9rem;

        box-shadow: 0 1px 4px rgba(0,0,0,0.06);

        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background-color: #f1f1f1;

        border-color: #c7c7c7;

        color: #0f0f0f;

        transform: translateY(-1px);
    }

    /* =========================
       CHAT INPUT
    ========================= */

    .stChatInput textarea {
        background-color: #ffffff !important;

        color: #0f0f0f !important;

        border-radius: 999px !important;

        border: 1px solid #d1d5db !important;

        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }

    /* =========================
       MENSAJES CHAT
    ========================= */

    [data-testid="stChatMessage"] {
        background: transparent;
    }

    [data-testid="stChatMessageContent"] {
        color: #0f0f0f;
    }

    /* =========================
       OCULTAR STREAMLIT
    ========================= */

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        visibility: hidden;
    }

    /* =========================
       SIDEBAR TIPO YOUTUBE
    ========================= */
    
    [data-testid="stSidebar"] {
        background-color: #f2f2f2;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem;
    }
    
    .sidebar-title {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1.4rem;
    }
    
    .sidebar-logo {
        width: 34px;
        height: 34px;
        border-radius: 8px;
        background: #ff0000;
        color: white;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.85rem;
        font-weight: 800;
    }
    
    .sidebar-main-title {
        font-size: 0.95rem;
        font-weight: 800;
        color: #0f0f0f;
    }
    
    .sidebar-subtitle {
        font-size: 0.72rem;
        color: #8a8a8a;
    }
    
    .sidebar-section-title {
        font-size: 0.68rem;
        font-weight: 800;
        color: #9ca3af;
        letter-spacing: 0.08rem;
        margin: 1rem 0 0.7rem 0;
    }
    
    .sidebar-item {
        background: transparent;
        border-radius: 12px;
        padding: 0.6rem 0.55rem;
        margin-bottom: 0.25rem;
        color: #0f0f0f;
        font-size: 0.82rem;
        display: grid;
        grid-template-columns: 28px 1fr;
        column-gap: 0.45rem;
        align-items: center;
    }
    
    .sidebar-item:hover {
        background: #e5e5e5;
    }
    
    .sidebar-item span {
        font-weight: 700;
    }
    
    .sidebar-item small {
        grid-column: 2;
        color: #8a8a8a;
        font-size: 0.72rem;
        margin-top: -0.1rem;
    }
    
    .sidebar-divider {
        height: 1px;
        background: #dddddd;
        margin: 1rem 0;
    }
    
    .data-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 0.75rem;
        font-size: 0.78rem;
        color: #0f0f0f;
    }
    
    .data-card div {
        display: flex;
        flex-direction: column;
        gap: 0.15rem;
        margin-bottom: 0.55rem;
    }
    
    .data-card div:last-child {
        margin-bottom: 0;
    }
    
    .data-card b {
        color: #6b7280;
        font-size: 0.7rem;
    }
    
    .data-card span {
        font-family: monospace;
        background: #f3f4f6;
        padding: 0.15rem 0.35rem;
        border-radius: 6px;
        color: #059669;
    }

    /* =========================
       WELCOME CARD
    ========================= */
    
    .welcome-card {
        background: #ffffff;
    
        border: 1px solid #e5e7eb;
    
        border-radius: 22px;
    
        padding: 1.2rem 1.3rem;
    
        margin-bottom: 1.4rem;
    
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    
    .welcome-top {
        display: flex;
        align-items: flex-start;
        gap: 1rem;
    }
    
    .welcome-icon {
        width: 42px;
        height: 42px;
    
        border-radius: 14px;
    
        background: linear-gradient(
            135deg,
            #ff0033,
            #ff4d6d
        );
    
        color: white;
    
        display: flex;
        align-items: center;
        justify-content: center;
    
        font-size: 1rem;
    
        flex-shrink: 0;
    }
    
    .welcome-title {
        font-size: 1rem;
        font-weight: 800;
        color: #0f0f0f;
        margin-bottom: 0.25rem;
    }
    
    .welcome-subtitle {
        font-size: 0.82rem;
        line-height: 1.5;
        color: #6b7280;
    }
    
    .welcome-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.6rem;
    
        margin-top: 1rem;
    }
    
    .welcome-tag {
        background: #f3f4f6;
    
        border: 1px solid #e5e7eb;
    
        border-radius: 999px;
    
        padding:
            0.4rem
            0.8rem;
    
        font-size: 0.74rem;
    
        font-weight: 600;
    
        color: #374151;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================
# 5. ENCABEZADO
# =========================

st.markdown('<div class="yt-header-wrapper">', unsafe_allow_html=True)

col_logo, col_text, col_status, col_videos = st.columns([0.35, 3, 1, 0.9])

with col_logo:
    st.markdown('<div class="yt-logo">▶</div>', unsafe_allow_html=True)

with col_text:
    st.markdown(
        """
        <div class="yt-title">Las Damitas Histeria</div>
        <div class="yt-subtitle">Agente de análisis · Powered by Gemini</div>
        """,
        unsafe_allow_html=True
    )

with col_status:
    st.markdown('<div class="yt-pill">🟢 Gemini conectado</div>', unsafe_allow_html=True)

with col_videos:
    st.markdown('<div class="yt-pill">📊 299 videos</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)


# =========================
# 6. SIDEBAR
# =========================

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-title">
            <span class="sidebar-logo">▶</span>
            <div>
                <div class="sidebar-main-title">Las Damitas Histeria</div>
                <div class="sidebar-subtitle">Agente YouTube Analytics</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="sidebar-section-title">ACCESOS RÁPIDOS</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="sidebar-item">🏆 <span>Top videos</span><small>Ranking por vistas</small></div>
        <div class="sidebar-item">📅 <span>Mejor día para publicar</span><small>Análisis de rendimiento</small></div>
        <div class="sidebar-item">🎯 <span>Temas más exitosos</span><small>Por engagement</small></div>
        <div class="sidebar-item">📈 <span>Resumen del canal</span><small>Stats generales</small></div>
        <div class="sidebar-item">🎬 <span>Formatos que funcionan</span><small>Shorts vs podcasts</small></div>
        <div class="sidebar-item">💗 <span>Mayor engagement</span><small>Likes y comentarios</small></div>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-title">PROBAR CONEXIÓN</div>', unsafe_allow_html=True)

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

    if st.button("Limpiar conversación", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# =========================
# 7. MENSAJE INFORMATIVO
# =========================

st.markdown("""
<div class="welcome-card">
    <div class="welcome-top">
        <div class="welcome-icon">✨</div>
        <div>
            <div class="welcome-title">¿Qué puede hacer este agente?</div>
            <div class="welcome-subtitle">
                Consulta métricas, rendimiento, temas, transcripciones y recomendaciones del canal usando lenguaje natural.
            </div>
        </div>
    </div>

    <div class="welcome-tags">
        <div class="welcome-tag">📊 Analytics</div>
        <div class="welcome-tag">🎬 Videos</div>
        <div class="welcome-tag">🔥 Engagement</div>
        <div class="welcome-tag">🧠 Gemini AI</div>
        <div class="welcome-tag">📈 Predicciones</div>
    </div>
</div>
""", unsafe_allow_html=True)


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

prompt = st.chat_input(
    "Ej: ¿Qué temas tienen mejor interacción en el canal?"
)

if prompt:
    # Mostrar mensaje del usuario
    st.chat_message("user").markdown(prompt)

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    # Generar respuesta del agente
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
                    "Revisa que tus Secrets estén configurados correctamente "
                    "y que la cuenta de servicio tenga permisos para BigQuery."
                )

                st.error(mensaje_error)
                st.exception(e)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": mensaje_error
                    }
                )
