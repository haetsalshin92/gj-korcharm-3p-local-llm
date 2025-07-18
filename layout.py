# layout.py
import streamlit as st

def render_sidebar():
    st.sidebar.title("local LLM 서비스")
    selected = st.sidebar.radio(
        "기능 선택",
        ["질문하기", "파일 정리"]
    )
    return selected
