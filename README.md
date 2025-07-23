# gj-korcharm-3p-local-llm

## 소개
이 프로젝트는 Streamlit 기반의 로컬 LLM 챗봇과 폴더 정리 도구를 제공합니다.

- **챗봇**: MongoDB에 대화 내역을 저장하며, LM Studio API를 통해 답변을 생성합니다.
- **파일 정리기**: 지정한 폴더 내 파일들을 이름별로 하위 폴더로 이동시켜 정리합니다.

## 주요 파일
- [`app.py`](app.py): Streamlit 앱 진입점. 챗봇 UI 실행.
- [`question.py`](question.py): 챗봇 UI 및 MongoDB 연동, LM Studio API 호출.

## 환경 변수 설정
`.env` 파일에서 데이터베이스 및 LM Studio API 정보를 설정합니다.
예시:
```
DATABASE_HOST=localhost
DATABASE_USER=root
DATABASE_PASSWORD=1234
DATABASE_NAME=streamlit

LM_STUDIO_URL=http://localhost:1234/v1/chat/completions
LM_STUDIO_MODEL=gemma-3-1b-it-qat

MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=chatdb
MONGODB_COLLECTION=conversations
```

## 실행 방법

1. 의존성 설치:
   ```sh
   pip install streamlit pymongo python-dotenv requests
   ```

2. Streamlit 앱 실행:
   ```sh
   streamlit run app.py
   ```

3. 웹 브라우저에서 안내된 주소로 접속하여 챗봇 및 파일 정리 기능 사용

## 기타
- LM Studio 및 MongoDB가 로컬에서 실행 중이어야 합니다.
- 환경 변수는 필요에 따라 수정합니다.