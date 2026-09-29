import os
import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb


upload_folder = "uploads"
files = os.listdir(upload_folder)
file_path = os.path.join(upload_folder, files[0])
 
print("File found:", file_path)

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
collection = client.get_or_create_collection(name="test_collection")
 
ids = [f"chunk_{i}" for i in range(len(chunks))]
collection.add(
    ids=ids,
    documents=chunks,
    embeddings=embeddings.tolist(),
)
 
print("Stored in Chroma. Count:", collection.count())