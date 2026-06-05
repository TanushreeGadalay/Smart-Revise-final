from sentence_transformers import SentenceTransformer
from pymongo import MongoClient

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["smartrevise"]

# list of all subject collections
collections = {
    "c": db["c_library"],
    "cpp": db["cpp_library"],
    "java": db["java_library"],
    "python": db["python_library"],
    "javascript": db["javascript_library"]
}


for subject, collection in collections.items():

    documents = list(collection.find({"embedding": {"$exists": False}}))

    if not documents:
        print(f"No new documents found for {subject}")
        continue

    print(f"Processing {len(documents)} documents for {subject}...")

    for doc in documents:

        text = doc.get("content", "")

        if not text:
            continue

        embedding = model.encode(text).tolist()

        collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"embedding": embedding}}
        )

    print(f"Embeddings completed for {subject}")

print("\nAll embeddings updated successfully!")