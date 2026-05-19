# -*- coding: utf-8 -*-

import os

import streamlit as st


# =========================
# 1. CONFIGURACION DE PAGINA
# =========================

st.set_page_config(
    page_title="Agente YouTube Analytics",
    page_icon="📊",
    layout="centered",
)


# =========================
# 2. CREDENCIALES
# =========================

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

if "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]

if not os.environ.get("GOOGLE_API_KEY"):
    st.error("Error critico: no se encontro GOOGLE_API_KEY en Secrets o en el archivo .env.")
    st.stop()

if "gcp_service_account" not in st.secrets:
    st.warning(
        "No se encontro gcp_service_account en Streamlit Secrets. "
        "En local se intentara usar credenciales de Google ADC."
    )


# =========================
# 3. IMPORTACION DEL AGENTE
# =========================

try:
    from agent import agent
except Exception as e:
    st.error("Error al importar el agente desde agent.py.")
    st.exception(e)
    st.stop()


# =========================
# 4. ESTILOS
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
        font-size: 2.2rem;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 0.35rem;
    }

    .subtitle {
        font-size: 1rem;
        color: #64748b;
        margin-bottom: 1.2rem;
    }

    .info-box {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e2e8f0;
        margin-bottom: 1.2rem;
    }

    .small-text {
        color: #64748b;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================
# 5. ENCABEZADO
# =========================

st.markdown(
    '<div class="main-title">📊 Agente Inteligente para YouTube</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="subtitle">
    Consulta el canal en lenguaje natural. El agente usa BigQuery, Gemini y busqueda semantica
    sobre segmentos de transcripcion para encontrar videos y minutos aproximados.
    </div>
    """,
    unsafe_allow_html=True,
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
    st.markdown("### Diagnostico")

    if st.button("Probar BigQuery"):
        with st.spinner("Verificando conexion con BigQuery..."):
            try:
                info = retriever.test_connection()
                st.success("Conexion exitosa")
                st.write("**Tabla:**", info["tabla"])
                st.write("**Filas:**", info["filas"])
                st.write("**Columnas:**", info["columnas"])
            except Exception as e:
                st.error("No se pudo conectar con BigQuery.")
                st.exception(e)

    if st.button("Reconstruir indice semantico"):
        with st.spinner("Segmentando y vectorizando transcripciones..."):
            try:
                segment_count = rebuild_semantic_index()
                st.success(f"Indice reconstruido con {segment_count} segmentos.")
            except Exception as e:
                st.error("No se pudo reconstruir el indice semantico.")
                st.exception(e)

    st.markdown("---")
    st.markdown("### Preguntas sugeridas")
    st.markdown(
        """
        - ¿En que video hable sobre dinero?
        - ¿En que minuto hablaron de familia?
        - ¿Que videos tienen mas views?
        - ¿Que temas tienen mejor interaccion?
        - ¿Que mejorarias del canal?
        - ¿Que videos rindieron peor de lo esperado?
        """
    )

    st.markdown("---")

    if st.button("Limpiar conversacion"):
        st.session_state.messages = []
        st.rerun()


# =========================
# 7. MENSAJE INFORMATIVO
# =========================

st.markdown(
    """
    <div class="info-box">
        <b>Busqueda mejorada:</b><br>
        <span class="small-text">
        Para preguntas como "En que video hable de X", el agente busca dentro de fragmentos
        vectorizados de la transcripcion, no solo en la clasificacion del video.
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================
# 8. MEMORIA DE CONVERSACION
# =========================

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hola. Soy tu agente de analisis de YouTube. "
                "Puedo buscar temas dentro de transcripciones, ubicar minutos aproximados "
                "y analizar metricas del canal."
            ),
        }
    ]


# =========================
# 9. HISTORIAL
# =========================

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# =========================
# 10. PREGUNTA DEL USUARIO
# =========================

prompt = st.chat_input("Ej: ¿En que video hable sobre productividad?")

if prompt:
    history_before_answer = st.session_state.messages[-8:]

    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Buscando en BigQuery y transcripciones vectorizadas..."):
            try:
                answer_text = agent.answer(prompt, history=history_before_answer)
                st.markdown(answer_text)
                st.session_state.messages.append({"role": "assistant", "content": answer_text})
            except Exception as e:
                error_message = (
                    "**Ocurrio un error al procesar tu pregunta:**\n\n"
                    f"`{str(e)}`\n\n"
                    "Revisa Secrets, permisos de BigQuery y que el indice semantico pueda construirse."
                )
                st.error(error_message)
                st.exception(e)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
