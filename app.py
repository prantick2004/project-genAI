import os
import streamlit as st

st.set_page_config(page_title="Chat with your file")
st.title("Chat with your file")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

if "done" not in st.session_state:
    st.session_state.done = False
if "messages" not in st.session_state:
    st.session_state.messages = []


def get_answer(question, file_path):
    # TODO: put your AI code here (whisper/pdf + LLM)
    return f"(demo) You asked: {question}"


if not st.session_state.done:
    file = st.file_uploader(
        "Upload audio, video or PDF",
        type=["mp3", "wav", "m4a", "mp4", "mov", "mkv", "pdf"],
    )
    if file and st.button("Done"):
        saved_path = os.path.join(UPLOAD_DIR, file.name)
        with open(saved_path, "wb") as f:
            f.write(file.getvalue())

        print("File saved:", saved_path)
        print("Size (KB):", os.path.getsize(saved_path) // 1024)

        st.session_state.file_name = file.name
        st.session_state.file_path = saved_path
        st.session_state.done = True
        st.rerun()

else:
    st.caption(f"File: {st.session_state.file_name}")

    if st.button("Upload new file"):
        st.session_state.clear()
        st.rerun()

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    if question := st.chat_input("Ask about your file..."):
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                answer = get_answer(
                    question,
                    st.session_state.file_path,
                )
            st.write(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})