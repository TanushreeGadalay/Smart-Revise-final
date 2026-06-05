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