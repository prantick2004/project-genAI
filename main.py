import streamlit as st

st.set_page_config(page_title="upload your file and chat", page_icon=":robot:")
st.title("upload your file and chat")


if "done" not in st.session_state:
    st.session_state.done = False
if "messages" not in st.session_state:
    st.session_state.messages = []


def get_answer(question, file_name, file_bytes):
    # TODO: put your AI code here (whisper + LLM)
    return f"(demo) You asked: {question}"


# ---------- step 1: upload ----------
if not st.session_state.done:
    file = st.file_uploader(
        "Upload pdf, audio or video",
        type=["mp3", "mp4", "pdf"],
    )
    if file and st.button("Done"):
        st.session_state.file_name = file.name
        st.session_state.file_bytes = file.getvalue()
        st.session_state.done = True
        st.rerun()

# ---------- step 2: chat ----------
else:
    st.caption(f"File: {st.session_state.file_name}")

    if st.button("Upload new file"):
        st.session_state.clear()
        st.rerun()

    # show old messages
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    # new message
    if question := st.chat_input("Ask about your file..."):
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                answer = get_answer(
                    question,
                    st.session_state.file_name,
                    st.session_state.file_bytes,
                )
            st.write(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})