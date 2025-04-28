import os
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup environment variables
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Ensure this is set in your .env
COLLECTION_NAME = "personal_knowledge"

# Initialize clients
qdrant_client = QdrantClient(url=QDRANT_URL)
embedding_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
llm = OpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)

# Function to create collection if not exists
def create_collection():
    existing = qdrant_client.get_collections().collections
    if COLLECTION_NAME not in [col.name for col in existing]:
        qdrant_client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )

# Function to split large text into chunks
def chunk_text(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    return splitter.split_text(text)

# Function to ingest document
def ingest_document(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    chunks = chunk_text(text)
    embeddings = embedding_model.embed_documents(chunks)

    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            {
                "id": idx,
                "vector": embedding,
                "payload": {"text": chunk}
            }
            for idx, (embedding, chunk) in enumerate(zip(embeddings, chunks))
        ]
    )

# Function to retrieve answers from vector search
def retrieve_answer(query):
    query_embedding = embedding_model.embed_query(query)

    hits = qdrant_client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_embedding,
        limit=5
    )

    relevant_contexts = "\n\n".join([hit.payload["text"] for hit in hits])

    prompt_template = PromptTemplate(
        input_variables=["context", "question"],
        template="""Use the following context to answer the question.

Context:
{context}

Question: {question}

Helpful Answer:"""
    )

    final_prompt = prompt_template.format(context=relevant_contexts, question=query)
    return llm(final_prompt)
