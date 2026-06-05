from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

client = MongoClient("mongodb://localhost:27017/")
db = client["smartrevise"]


def get_collection_from_query(query):

    q = query.lower()

    if q.startswith("c++"):
        return db["cpp_library"]

    elif q.startswith("c:") or q.startswith("c "):
        return db["c_library"]

    elif q.startswith("java"):
        return db["java_library"]

    elif q.startswith("python"):
        return db["python_library"]

    elif q.startswith("javascript"):
        return db["javascript_library"]

    else:
        return db["cpp_library"]


def semantic_search(query):

    collection = get_collection_from_query(query)

    # remove subject prefix
    query_clean = query.split(":", 1)[-1]

    query_embedding = model.encode(query_clean)

    docs = collection.find()

    similarities = []

    for doc in docs:

        if "embedding" not in doc:
            continue

        emb = np.array(doc["embedding"])

        similarity = np.dot(query_embedding, emb) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(emb)
        )

        similarities.append((similarity, doc["content"]))


    similarities.sort(reverse=True)

    top_results = similarities[:1]

    context = "\n".join([text for _, text in top_results])

    return context