import os
import pdfplumber
from pymongo import MongoClient

# connect to mongodb
client = MongoClient("mongodb://localhost:27017/")
db = client["smartrevise"]
collection = db["cpp_library"]

pdf_path = "cpp_notes.pdf"

if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) == 0:
    print(f"Error: The file '{pdf_path}' does not exist or is empty.")
    exit(1)

full_text = ""

# extract text from pdf
try:
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
except Exception as e:
    print(f"Error reading PDF: {e}")
    exit(1)

# split content into chunks

chunk_size = 500
chunks = []

for i in range(0, len(full_text), chunk_size):
    chunk = full_text[i:i + chunk_size]
    chunks.append(chunk)

documents = []

for chunk in chunks:
    if len(chunk.strip()) > 100:
        documents.append({
            "subject": "cpp",
            "chunk_id": len(documents),
            "content": chunk.strip()
        })

# insert into database
if documents:
    collection.insert_many(documents)
    print(f"Extraction completed. Inserted {len(documents)} document chunks.")
else:
    print("Extraction completed. No valid document chunks found to insert.")