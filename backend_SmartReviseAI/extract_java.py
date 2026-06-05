import os
import pdfplumber
from pymongo import MongoClient

# connect to mongodb
client = MongoClient("mongodb://localhost:27017/")
db = client["smartrevise"]

# collection for Java
collection = db["java_library"]

pdf_path = "Java_notes.pdf"

if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) == 0:
    print(f"Error: {pdf_path} not found or empty")
    exit(1)

full_text = ""

# extract text
try:
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
except Exception as e:
    print("PDF read error:", e)
    exit(1)


# split into chunks
chunk_size = 500
chunks = []

for i in range(0, len(full_text), chunk_size):
    chunk = full_text[i:i+chunk_size]
    chunks.append(chunk)


documents = []

for chunk in chunks:
    if len(chunk.strip()) > 100:
        documents.append({
            "subject": "java",
            "chunk_id": len(documents),
            "content": chunk.strip()
        })


if documents:
    collection.insert_many(documents)
    print(f"Inserted {len(documents)} Java chunks")
else:
    print("No valid Java chunks found")