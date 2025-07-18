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
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["chatdb"]
collection = db["conversations"]

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
    st.title("🧠 LM Studio 대화형 AI")

    # 쿼리 파라미터 읽기
    query_params = st.query_params

    selected_id = None
    if "convo" in query_params and query_params["convo"]:

        print(f"디버그: query_params['convo']의 전체 값: {query_params['convo']}")
        print(f"디버그: query_params['convo']의 타입: {type(query_params['convo'])}")

        candidate = query_params["convo"]
        print(f"디버그: candidate: {candidate}")
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

    # 새 채팅 시작 버튼
    if st.sidebar.button("➕ 새 채팅 시작"):
        st.query_params = {}  # 쿼리 파라미터 초기화
        st.session_state.selected_convo_id = None
        st.rerun()  # rerun 대신 페이지가 리로드되므로 없어도 되지만 안전하게 호출

    # 대화 목록 출력 (버튼)
    convos = list(collection.find().sort("created_at", -1))
    for convo in convos:
        display_title = convo.get("title") or "(제목 없음)"
        if st.sidebar.button(display_title, key=str(convo["_id"])):
            st.query_params = {"convo": str(convo["_id"])}
            st.rerun()

    # 선택된 대화 보여주기 및 메시지 입력 처리
    if st.session_state.selected_convo_id:
        convo = collection.find_one({"_id": ObjectId(st.session_state.selected_convo_id)})
        if convo is None:
            st.error("선택한 대화가 존재하지 않습니다.")
            st.session_state.selected_convo_id = None
            st.query_params = {}
            st.rerun()
            return

        st.subheader(f"💬 {convo['title']}")
        for msg in convo.get("messages", []):
            with st.chat_message(msg["role"], avatar="🌀" if msg["role"] == "user" else "🤖"):
                st.markdown(msg["content"])

        user_input = st.chat_input("메시지를 입력하세요")
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

    else:
        st.subheader("➕ 새 채팅을 시작하려면 질문을 입력하세요")
        user_input = st.chat_input("메시지를 입력하세요")
        if user_input:
            # 1. 신규 대화 생성 및 사용자 메시지 저장
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

            # 2. LLM API 호출
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

            # 3. 어시스턴트 답변 DB 저장
            assistant_msg = {"role": "assistant", "content": answer, "timestamp": datetime.utcnow()}
            collection.update_one(
                {"_id": ObjectId(new_id)},
                {"$push": {"messages": assistant_msg}}
            )

            # 4. 쿼리 파라미터에 대화 ID 유지, 리런
            st.query_params = {"convo": new_id}
            st.rerun()

if __name__ == "__main__":
    run_question_ui()
