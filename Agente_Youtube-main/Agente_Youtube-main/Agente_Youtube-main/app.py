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
    /* Fondo general */
    .stApp {
        background-color: #f7f7f7;
        color: #0f0f0f;
    }

    /* Contenedor principal */
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 6rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
    }

    /* Tipografía general */
    html, body, [class*="css"] {
        font-family: "Inter", "Segoe UI", sans-serif;
    }

    /* Título superior */
    .main-title {
        font-size: 1.45rem;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 0.15rem;
        color: #0f0f0f;
    }

    .subtitle {
        font-size: 0.82rem;
        color: #6b7280;
        margin-bottom: 0;
    }

    /* Caja informativa */
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

    /* Botones */
    .stButton > button {
        border-radius: 999px;
        border: 1px solid #d1d5db;
        background-color: #ffffff;
        color: #374151;
        font-weight: 600;
        padding: 0.45rem 0.9rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background-color: #f1f1f1;
        border-color: #c7c7c7;
        color: #0f0f0f;
        transform: translateY(-1px);
    }

    /* Input inferior */
    .stChatInput textarea {
        background-color: #ffffff !important;
        color: #0f0f0f !important;
        border-radius: 999px !important;
        border: 1px solid #d1d5db !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }

    /* Mensajes del chat */
    [data-testid="stChatMessage"] {
        background: transparent;
    }

    [data-testid="stChatMessageContent"] {
        color: #0f0f0f;
    }

    /* Ocultar menú superior de Streamlit si molesta */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =========================
# 5. ENCABEZADO
# =========================

st.markdown(
    """
    <div class="top-header">

        <div class="header-left">
            <div class="youtube-logo">
                ▶
            </div>

            <div>
                <div class="main-title">
                    Las Damitas Histeria
                </div>

                <div class="subtitle">
                    Agente de análisis • Powered by Gemini
                </div>
            </div>
        </div>

        <div class="header-right">

            <div class="status-pill">
                🟢 Gemini conectado
            </div>

            <div class="status-pill">
                📊 299 videos
            </div>

        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# =========================
# 6. SIDEBAR
# =========================

with st.sidebar:
    st.title("⚙️ Panel del agente")

    st.markdown("### Fuente de datos")
    st.markdown(
        """
        **Proyecto:** `mineria-datos-493000`  
        **Dataset:** `youtube`  
        **Tabla:** `fact_final`
        """
    )

    st.markdown("---")

    st.markdown("### Probar conexión")

    if st.button("Probar BigQuery"):
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

    st.markdown("---")

    st.markdown("### Preguntas sugeridas")

    st.markdown(
        """
        - ¿Cuál es el resumen del canal?
        - ¿Qué videos tienen más views?
        - ¿Qué temas tienen mejor interacción?
        - ¿En qué video hablaron de productividad?
        - ¿Qué mejorarías del canal?
        - ¿Qué videos rindieron peor de lo esperado?
        """
    )

    st.markdown("---")

    if st.button("Limpiar conversación"):
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
