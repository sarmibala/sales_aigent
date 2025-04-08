# app/azure_search.py
import os
import numpy as np
import json
import requests
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    VectorSearchAlgorithmConfiguration
)

AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME")
AZURE_SEARCH_API_VERSION = os.getenv("AZURE_SEARCH_API_VERSION")

# === Create Search Index ===
def create_vector_index(dim=3072):
    credential = AzureKeyCredential(AZURE_SEARCH_KEY)
    index_client = SearchIndexClient(endpoint=AZURE_SEARCH_ENDPOINT, credential=credential)  

    # # Skip creation if it already exists
    # if AZURE_SEARCH_INDEX_NAME in [idx.name for idx in index_client.list_indexes()]:
    #     print(f"Index '{AZURE_SEARCH_INDEX_NAME}' already exists. Skipping creation.")
    #     return
    
    fields = [
        SearchField(name="id", type=SearchFieldDataType.String, key=True),
        SearchField(name="content", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="embedding", type="Collection(Edm.Single)", searchable=True,
                    vector_search_dimensions=dim, vector_search_profile_name="default"),
        SearchField(name="metadata", type=SearchFieldDataType.String, searchable=False)
    ]

    vector_search = VectorSearch(
        profiles=[
            VectorSearchProfile(name="default", algorithm_configuration_name="my-hnsw")
        ],
        algorithm_configurations=[
            VectorSearchAlgorithmConfiguration(name="my-hnsw", kind="hnsw")
        ]
    )

    index = SearchIndex(name=AZURE_SEARCH_INDEX_NAME, fields=fields, vector_search=vector_search)
    try:
        index_client.delete_index(AZURE_SEARCH_INDEX_NAME)
    except:
        pass
    index_client.create_index(index)
    print(f"Created index '{AZURE_SEARCH_INDEX_NAME}' with HNSW vector search.")

# === Upload Embeddings ===
def upload_documents_to_search(pdf_name, texts, vectors, metadata):
    credential = AzureKeyCredential(AZURE_SEARCH_KEY)
    search_client = SearchClient(endpoint=AZURE_SEARCH_ENDPOINT,
                                 index_name=AZURE_SEARCH_INDEX_NAME,
                                 credential=credential)

    documents = []
    for i in range(len(texts)):
        documents.append({
            "id": f"{pdf_name}-{i}",
            "content": texts[i],
            "embedding": vectors[i].tolist(),
            "metadata": json.dumps(metadata[i]) if i < len(metadata) else "{}"
        })

    result = search_client.upload_documents(documents)
    print(f"Uploaded {len(result)} documents to Azure Cognitive Search.")


# === Vector Search from Azure Search ===
def search_similar_content(query_vector, top_k=10):
    credential = AzureKeyCredential(AZURE_SEARCH_KEY)
    search_client = SearchClient(AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_INDEX_NAME, credential)

    results = search_client.search(  
        search_text=None,  
        vector_queries= [query_vector], 
        select=["id", "content"],
        top=top_k 
    )
    print(f"search_similar_content Results: {results}")  
    
    top_chunks = []
    for result in results:
        print(f"🔹 ID: {result['id']}")
        print(f"📝 Content Preview: {result['content'][:150]}...\n")
        top_chunks.append(result["content"])

    return top_chunks