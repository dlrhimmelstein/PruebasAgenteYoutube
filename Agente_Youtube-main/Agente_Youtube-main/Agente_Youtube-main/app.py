import os
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Agente YouTube Analytics",
    page_icon="📊",
    layout="wide"
)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

if "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]

if "GOOGLE_API_KEY" not in os.environ:
    st.error("No se encontró GOOGLE_API_KEY")
    st.stop()

from agent import agent

with open("interfaz_agente_yt.html", "r", encoding="utf-8") as f:
    html_code = f.read()

components.html(
    html_code,
    height=850,
    scrolling=True
)

prompt = st.chat_input("Pregunta sobre el canal")

if prompt:
    st.chat_message("user").markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Consultando BigQuery y Gemini..."):
            respuesta = agent.answer(prompt)

        st.markdown(respuesta)
