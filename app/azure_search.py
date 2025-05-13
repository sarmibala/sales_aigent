# app/azure_search.py

import os
import json
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv
load_dotenv()

AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
# AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME")
AZURE_SEARCH_API_VERSION = os.getenv("AZURE_SEARCH_API_VERSION")

# === Upload Embeddings ===
def upload_documents_to_search(index_name, pdf_name, texts, vectors, metadata):
    credential = AzureKeyCredential(AZURE_SEARCH_KEY)
    search_client = SearchClient(endpoint=AZURE_SEARCH_ENDPOINT, index_name=index_name, credential=credential)

    documents = []
    for i in range(len(texts)):
        documents.append({
            "id": f"{pdf_name}-{i}",
            "content": texts[i],
            "embedding": vectors[i].tolist(),
            "metadata": json.dumps(metadata[i]) if i < len(metadata) else "{}",
            "surface_type": metadata[i].get("surface_type", index_name),
            "collection_name": metadata[i].get("collection_name", ""),
            "product_type": metadata[i].get("product_type", "")
        })

    result = search_client.upload_documents(documents)
    print(f"Uploaded {len(result)} documents to Azure Cognitive Search.")


# === Vector Search from Azure Search ===
def search_similar_content(query_vector, index_name, top_k=10):
    credential = AzureKeyCredential(AZURE_SEARCH_KEY)
    search_client = SearchClient(AZURE_SEARCH_ENDPOINT, index_name, credential)
    results = search_client.search(search_text=None, vector_queries=[query_vector], select=["id", "content"], top=top_k)
    return [result["content"] for result in results]