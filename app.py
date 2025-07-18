# app.py
import streamlit as st
from layout import render_sidebar
from question import run_question_ui
from file_organizer import run_file_organizer_ui

st.set_page_config(page_title="local LLM", layout="wide")

selected_page = render_sidebar()

if selected_page == "질문하기":
    run_question_ui()
elif selected_page == "파일 정리":
    run_file_organizer_ui()
