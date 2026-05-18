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

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 950px;
    }

    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 0.3rem;
    }

    .subtitle {
        font-size: 1rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }

    .info-box {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 0.8rem;
        border: 1px solid #e2e8f0;
        margin-bottom: 1.2rem;
    }

    .small-text {
        color: #64748b;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================
# 5. ENCABEZADO
# =========================

st.markdown(
    '<div class="main-title">📊 Agente Inteligente para YouTube</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="subtitle">
    Consulta información del canal usando lenguaje natural. 
    El agente recupera datos desde BigQuery, analiza métricas y genera respuestas con Gemini.
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
