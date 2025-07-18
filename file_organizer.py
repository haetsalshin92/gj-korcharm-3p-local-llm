import os
import shutil
import streamlit as st

def run_file_organizer_ui():
    st.header("📂 폴더 정리")
    target_dir = st.text_input("정리할 대상 폴더 경로", value=os.path.expanduser("~"))
    organize_button = st.button("폴더 정리 시작")

    if organize_button:
        if not os.path.exists(target_dir):
            st.error("❌ 입력한 경로가 존재하지 않습니다.")
            return

        files = [f for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f))]

        if not files:
            st.info("📭 폴더 내에 정리할 파일이 없습니다.")
            return

        for file_name in files:
            src_path = os.path.join(target_dir, file_name)
            name_only, _ = os.path.splitext(file_name)
            dest_folder = os.path.join(target_dir, name_only)

            try:
                os.makedirs(dest_folder, exist_ok=True)
                shutil.move(src_path, os.path.join(dest_folder, file_name))
            except Exception as e:
                st.error(f"❌ {file_name} 이동 중 오류 발생: {e}")
        
        st.success("✅ 파일 정리가 완료되었습니다.")


