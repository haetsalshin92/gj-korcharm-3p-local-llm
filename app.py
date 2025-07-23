# app.py
import streamlit as st
from question import run_question_ui

st.set_page_config(page_title="local LLM", layout="wide")

# 바로 질문 UI 실행
run_question_ui()
