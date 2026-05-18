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
       CANAL AL DÍA - SIDEBAR
    ========================= */
    
    .sidebar-spacer {
        height: 7rem;
    }
    
    .channel-status-card {
        border-top: 1px solid #dddddd;
        padding-top: 0.9rem;
        margin-top: 1rem;
    }
    
    .channel-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
    
        font-size: 0.78rem;
        margin-bottom: 0.65rem;
    }
    
    .channel-row span {
        color: #8a8a8a !important;
        font-weight: 500;
    }
    
    .channel-row b {
        color: #0f0f0f !important;
        font-weight: 700;
    }
    
    .agent-active {
        color: #e60023 !important;
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

    .welcome-tags-text {
        margin-top: 1rem;
        color: #374151;
        font-size: 0.78rem;
        font-weight: 600;
    }

    /* =========================
       MENSAJES DEL SIDEBAR
    ========================= */
    
    [data-testid="stSidebar"] .stSuccess {
        background-color: #dcfce7;
        color: #166534;
        border-radius: 10px;
    }
    
    [data-testid="stSidebar"] .stSuccess div {
        color: #166534;
    }
    
    [data-testid="stSidebar"] .stWrite,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {
        color: #0f0f0f;
    }
    
    .connection-info {
        margin-top: 0.8rem;
        color: #0f0f0f;
        font-size: 0.82rem;
    }
    
    .connection-info p {
        color: #0f0f0f !important;
        margin-bottom: 0.45rem;
    }
    
    .connection-info code {
        background: #111827;
        color: #22c55e;
        padding: 0.15rem 0.35rem;
        border-radius: 6px;
    }

    /* =========================
       BIENVENIDA INICIAL
    ========================= */
    
   .empty-logo,
    .empty-title,
    .empty-text {
        max-width: 560px;
        margin-left: auto;
        margin-right: auto;
        text-align: center;
    }
    
    .empty-logo {
        width: 64px;
        height: 48px;
        margin-top: 4rem;
        margin-bottom: 1.2rem;
        background: #ff0000;
        color: white;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        font-weight: 800;
        box-shadow: 0 8px 20px rgba(255,0,0,0.25);
    }
    
    .empty-title {
        font-size: 1.35rem;
        font-weight: 800;
        color: #111827;
        margin-bottom: 0.8rem;
    }
    
    .empty-text {
        font-size: 0.95rem;
        line-height: 1.6;
        color: #4b5563;
    }

     /* =========================
       CHAT INPUT FINAL
    ========================= */
    
    [data-testid="stBottom"] {
    
        background-color: #f1f3f4 !important;
    
        background-image: none !important;
    
        border-top: 1px solid #e5e7eb !important;
    
        padding: 0.8rem 2rem !important;
    
        box-shadow: none !important;
    }

    [data-testid="stBottom"]::before,
    [data-testid="stBottom"]::after {
        display: none !important;
    }
    
    [data-testid="stBottom"] > div {
        max-width: 1050px !important;
        margin: 0 auto !important;
    }
    
    [data-testid="stChatInput"] {
        background: transparent !important;
    }
    
    [data-testid="stChatInput"] > div {
        background: transparent !important;
    }
    
    [data-baseweb="textarea"] {
        border-radius: 999px !important;
    
        border: 1px solid #d1d5db !important;
    
        background: #ffffff !important;
    
        box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
    }
    
    [data-baseweb="textarea"] textarea {
    
        background: #ffffff !important;
    
        color: #111827 !important;
    
        font-size: 0.95rem !important;
    
        padding-top: 0.95rem !important;
    
        padding-left: 1.2rem !important;
    
        text-align: left !important;
    }
    
    [data-baseweb="textarea"] textarea::placeholder {
    
        color: #9ca3af !important;
    
        opacity: 1 !important;
    }

[data-testid="stChatInput"] button {

    background: #ff0000 !important;

    color: white !important;

    border-radius: 999px !important;

    border: none !important;
}

    /* Forzar fondo claro en la zona inferior */
    [data-testid="stBottom"],
    [data-testid="stBottom"] > div,
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] > div {
        background-color: #f1f3f4 !important;
        background: #f1f3f4 !important;
    }
    
    /* Mantener el input blanco */
    [data-baseweb="textarea"],
    [data-baseweb="textarea"] *,
    [data-baseweb="textarea"] textarea {
        background-color: #ffffff !important;
        background: #ffffff !important;
    }

    /* =========================
       MENSAJES CHAT
    ========================= */
    
    [data-testid="stChatMessage"] {
        background: transparent !important;
        padding: 0 !important;
    }
    
    [data-testid="stChatMessageContent"] {
        background: white;
    
        border: 1px solid #e5e7eb;
    
        border-radius: 18px;
    
        padding: 1rem 1.2rem;
    
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    
        margin-bottom: 1rem;
    }
    
    /* Usuario */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] {
        background: #2563eb;
        color: white;
        border: none;
    }
    
    /* =========================
       THINKING BOX
    ========================= */
    
    .thinking-box {
        display: flex;
        align-items: center;
        gap: 0.7rem;
    
        background: white;
    
        border: 1px solid #e5e7eb;
    
        border-radius: 16px;
    
        padding: 0.9rem 1rem;
    
        width: fit-content;
    
        color: #4b5563;
    
        font-size: 0.9rem;
    }
    
    .thinking-dot {
        width: 10px;
        height: 10px;
    
        border-radius: 999px;
    
        background: #ff0000;
    
        animation: pulse 1s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 0.4; transform: scale(0.9); }
        50% { opacity: 1; transform: scale(1.1); }
        100% { opacity: 0.4; transform: scale(0.9); }
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
    st.markdown('<div class="sidebar-spacer"></div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="channel-status-card">
            <div class="sidebar-section-title">CANAL AL DÍA</div>

            <div class="channel-row">
                <span>Videos</span>
                <b>299</b>
            </div>

            <div class="channel-row">
                <span>Views totales</span>
                <b>16.7M</b>
            </div>

            <div class="channel-row">
                <span>Likes totales</span>
                <b>716K</b>
            </div>

            <div class="channel-row">
                <span>Comentarios</span>
                <b>34.8K</b>
            </div>

            <div class="channel-row">
                <span>Estado del agente</span>
                <b class="agent-active">● Activo</b>
            </div>
        </div>
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

                st.markdown(f"""
                <div class="connection-info">
                    <p><b>Tabla:</b> <code>{info["tabla"]}</code></p>
                    <p><b>Filas:</b> <code>{info["filas"]}</code></p>
                    <p><b>Columnas:</b> <code>{info["columnas"]}</code></p>
                </div>
                """, unsafe_allow_html=True)

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

st.markdown(
    '<div class="welcome-card"><div class="welcome-top"><div class="welcome-icon">✨</div><div><div class="welcome-title">¿Qué puede hacer este agente?</div><div class="welcome-subtitle">Consulta métricas, rendimiento, temas, transcripciones y recomendaciones del canal usando lenguaje natural.</div></div></div><div class="welcome-tags-text">📊 Analytics &nbsp;&nbsp; 🎬 Videos &nbsp;&nbsp; 🔥 Engagement &nbsp;&nbsp; 🧠 Gemini AI &nbsp;&nbsp; 📈 Predicciones</div></div>',
    unsafe_allow_html=True
)


# =========================
# 8. MEMORIA DE CONVERSACIÓN
# =========================

if "messages" not in st.session_state:
    st.session_state.messages = []

if len(st.session_state.messages) == 0:
    st.markdown('<div class="empty-logo">▶</div>', unsafe_allow_html=True)
    st.markdown('<div class="empty-title">Hola, soy tu agente de YouTube</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="empty-text">Puedo analizar el rendimiento de <b>Las Damitas Histeria</b>, encontrar en qué episodio hablaron de un tema, decirte los mejores días para publicar y mucho más. ¡Pregúntame lo que necesites!</div>',
        unsafe_allow_html=True
    )


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
    "Pregunta sobre el canal... ej: ¿Qué temas tuvieron más engagement?"
)

if prompt:

    # Guardar mensaje usuario
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    # Mostrar usuario
    with st.chat_message("user"):
        st.markdown(prompt)

    # Respuesta del agente
    with st.chat_message("assistant"):

        thinking_placeholder = st.empty()

        thinking_placeholder.markdown(
            """
            <div class="thinking-box">
                <div class="thinking-dot"></div>
                Analizando métricas del canal...
            </div>
            """,
            unsafe_allow_html=True
        )

        try:

            respuesta_texto = agent.answer(prompt)

            thinking_placeholder.empty()

            st.markdown(respuesta_texto)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": respuesta_texto
                }
            )

        except Exception as e:

            thinking_placeholder.empty()

            mensaje_error = (
                "❌ Ocurrió un error al procesar tu pregunta.\n\n"
                f"`{str(e)}`"
            )

            st.error(mensaje_error)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": mensaje_error
                }
            )
