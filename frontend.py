import streamlit as st
from backend import create_collection, ingest_document, retrieve_answer
import os

# Ensure docs directory exists
os.makedirs("docs", exist_ok=True)

# Create collection at startup
create_collection()

st.set_page_config(page_title="Personal Knowledgebase Chatbot", layout="wide")
st.title("📚 Personal Knowledgebase Chatbot")

menu = st.sidebar.selectbox("Menu", ["Upload Document", "Ask a Question"])

if menu == "Upload Document":
    uploaded_file = st.file_uploader("Upload a text (.txt) document", type=["txt"])

    if uploaded_file is not None:
        file_path = os.path.join("docs", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        ingest_document(file_path)
        st.success("✅ Document uploaded and indexed successfully!")

elif menu == "Ask a Question":
    query = st.text_input("Ask your question:")
    if st.button("Get Answer"):
        if query:
            with st.spinner("Thinking..."):
                answer = retrieve_answer(query)
            st.success(answer)
        else:
            st.warning("⚡ Please enter a question.")
