import os
import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb
from google import genai
from dotenv import load_dotenv

upload_folder = "uploads"
files = os.listdir(upload_folder)
full_paths = [os.path.join(upload_folder, f) for f in files]
file_path = max(full_paths, key=os.path.getmtime)

#print("File found:", file_path)

#file_path = "/home/prantick/Desktop/project genAI/uploads/GenAI Project Problem Statement.pdf"

doc = fitz.open(file_path)
"""print("Pages:", len(doc))"""

text = ""
for page in doc:
    text += page.get_text()

#print(text)

text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
chunks = text_splitter.split_text(text)
"""print("Number of chunks:", len(chunks))
print("Sample chunk:", chunks[:])"""


embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
embeddings = embed_model.encode(chunks, normalize_embeddings=True)

"""print("Number of embeddings:", len(embeddings))
print("Embedding dimension:", len(embeddings[0]))
print("Sample embedding:", embeddings[0])"""


client = chromadb.PersistentClient(path="./chroma_db")
try:
    client.delete_collection("test_collection")
except Exception:
    pass
collection = client.get_or_create_collection(name="test_collection")

ids = [f"chunk_{i}" for i in range(len(chunks))]
collection.add(
    ids=ids,
    documents=chunks,
    embeddings=embeddings.tolist(),
)

#print("Stored in Chroma. Count:", collection.count())


query = input("\nAsk your question: ")
query_embedding = embed_model.encode(query, normalize_embeddings=True)

result = collection.query(query_embeddings=[query_embedding.tolist()],n_results=1,)

retrieved_chunks = result["documents"][0]

print("\nTop match chunks:")
for i, chunk in enumerate(retrieved_chunks, start=1):
    print(chunk)

context = "\n\n".join(retrieved_chunks)

prompt = f"""
You are a helpful document assistant. Answer the user's question using ONLY the information provided in the context below. If the answer can not be found in the context, say: "I could not find the answer in the given document."

Do not use your own knowledge or make up information.

Context:
{context}

User Question:
{query}

Answer:
"""

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents=prompt,
)
answer = response.text

print("\nFinal Answer:", answer)