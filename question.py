import streamlit as st
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId
import os
import json
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# MongoDB 연결
mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
mongo_db = os.getenv("MONGODB_DB", "chatdb")
mongo_collection = os.getenv("MONGODB_COLLECTION", "conversations")

mongo_client = MongoClient(mongo_uri)
db = mongo_client[mongo_db]
collection = db[mongo_collection]

# LM Studio API 정보
lm_studio_url = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1/chat/completions")
model = os.getenv("LM_STUDIO_MODEL", "gemma-3-1b-it-qat")

def is_valid_objectid(oid):
    try:
        ObjectId(oid)
        return True
    except (InvalidId, TypeError):
        return False


def run_question_ui():
    st.set_page_config(page_title='LM Studio Chat', page_icon='🤖')
    st.markdown(
        "<h1 style='text-align: center;'>🧠 LM Studio 대화형 AI</h1>",
        unsafe_allow_html=True
    )

    # 쿼리 파라미터 읽기
    query_params = st.query_params
    selected_id = None
    if "convo" in query_params and query_params["convo"]:
        candidate = query_params["convo"]
        if is_valid_objectid(candidate):
            selected_id = candidate
        else:
            st.error(f"잘못된 대화 ID입니다: {candidate}")
            st.query_params = {}  # 쿼리 파라미터 초기화
            selected_id = None

    if "selected_convo_id" not in st.session_state:
        st.session_state.selected_convo_id = None

    if selected_id != st.session_state.selected_convo_id:
        st.session_state.selected_convo_id = selected_id

    st.sidebar.header("💬 대화 목록")

    if st.sidebar.button("➕ 새 채팅 시작"):
        st.query_params = {}
        st.session_state.selected_convo_id = None
        st.rerun()

    # 대화 목록 출력
    convos = list(collection.find().sort("created_at", -1))
    for convo in convos:
        display_title = convo.get("title") or "(제목 없음)"
        convo_id_str = str(convo["_id"])
        is_selected = convo_id_str == st.session_state.selected_convo_id
        label = f"✅ {display_title}" if is_selected else display_title

        if st.sidebar.button(label, key=convo_id_str):
            st.query_params = {"convo": convo_id_str}
            st.rerun()

    # 🔻 공통 입력창 (한 번만 정의)
    user_input = st.chat_input("메시지를 입력하세요", key="unique_chat_input")

    # ✅ 기존 대화 선택된 경우
    if st.session_state.selected_convo_id:
        convo = collection.find_one({"_id": ObjectId(st.session_state.selected_convo_id)})
        if convo is None:
            st.error("선택한 대화가 존재하지 않습니다.")
            st.session_state.selected_convo_id = None
            st.query_params = {}
            st.rerun()
            return

        for msg in convo.get("messages", []):
            with st.chat_message(msg["role"], avatar="🌀" if msg["role"] == "user" else "🤖"):
                st.markdown(msg["content"])

        if user_input:
            user_msg = {"role": "user", "content": user_input, "timestamp": datetime.utcnow()}
            collection.update_one(
                {"_id": ObjectId(st.session_state.selected_convo_id)},
                {"$push": {"messages": user_msg}}
            )

            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("⏳ 답변 생성 중..."):
                    try:
                        headers = {"Content-Type": "application/json"}
                        body = {
                            "messages": [{"role": "user", "content": user_input}],
                            "temperature": 0.7,
                            "max_tokens": 1024,
                            "stream": False,
                            "model": model
                        }
                        response = requests.post(lm_studio_url, headers=headers, data=json.dumps(body))
                        response.raise_for_status()
                        answer = response.json()["choices"][0]["message"]["content"]
                        st.write(answer)
                    except Exception as e:
                        answer = f"❌ 오류 발생: {e}"
                        st.error(answer)

            assistant_msg = {"role": "assistant", "content": answer, "timestamp": datetime.utcnow()}
            collection.update_one(
                {"_id": ObjectId(st.session_state.selected_convo_id)},
                {"$push": {"messages": assistant_msg}}
            )

            st.query_params = {"convo": st.session_state.selected_convo_id}
            st.rerun()

    # 🆕 새 대화 시작
    else:
        st.subheader("➕ 새 채팅을 시작하려면 메시지를 입력하세요")
        if user_input:
            convo_doc = {
                "title": user_input[:50],
                "model": model,
                "created_at": datetime.utcnow(),
                "messages": [
                    {"role": "user", "content": user_input, "timestamp": datetime.utcnow()}
                ],
            }
            result = collection.insert_one(convo_doc)
            new_id = str(result.inserted_id)
            st.session_state.selected_convo_id = new_id

            answer = ""
            with st.spinner("⏳ 답변 생성 중..."):
                try:
                    headers = {"Content-Type": "application/json"}
                    body = {
                        "messages": [{"role": "user", "content": user_input}],
                        "temperature": 0.7,
                        "max_tokens": 1024,
                        "stream": False,
                        "model": model
                    }
                    response = requests.post(lm_studio_url, headers=headers, data=json.dumps(body))
                    response.raise_for_status()
                    answer = response.json()["choices"][0]["message"]["content"]
                    st.write(answer)
                except Exception as e:
                    answer = f"❌ 오류 발생: {e}"
                    st.error(answer)

            assistant_msg = {"role": "assistant", "content": answer, "timestamp": datetime.utcnow()}
            collection.update_one(
                {"_id": ObjectId(new_id)},
                {"$push": {"messages": assistant_msg}}
            )

            st.query_params = {"convo": new_id}
            st.rerun()


if __name__ == "__main__":
    run_question_ui()
