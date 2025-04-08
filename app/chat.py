import os
import numpy as np
from openai import AzureOpenAI
from app.azure_search import search_similar_content
from azure.search.documents.models import (
    QueryAnswerType,
    QueryCaptionType,
    QueryType,
    VectorizedQuery,
)

EMBEDDING_DIM = 3072

client = AzureOpenAI(
    api_version=os.getenv("AZURE_OPENAI_EMBEDDING_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY")
)

# Example function to generate document embedding
def generate_embeddings(text, model):
    # Generate embeddings for the provided text using the specified model
    embeddings_response = client.embeddings.create(model=model, input=text)
    # Extract the embedding data from the response
    embedding = embeddings_response.data[0].embedding
    return embedding

def chat_with_gpt(user_input: str):
    vector_query = VectorizedQuery(vector=generate_embeddings(user_input, os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")), k_nearest_neighbors=10, fields="embedding")
    print(f'User input ==> {user_input}')
    # print(f'query_vector ==> {vector_query}')

    # Search using Azure Cognitive Search
    top_chunks = search_similar_content(vector_query, top_k=5)
    print(f'Top chunks from Azure Search ==> {len(top_chunks)}')
    context = "\n\n".join(top_chunks)

    # Optional: Trimming context if too long
    max_context_length = 1500
    if len(context.split()) > max_context_length:
        context = ' '.join(context.split()[:max_context_length])

    # Ask GPT
    chat_response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT_NAME"),
        messages=[
            {"role": "system", "content": "You are a flooring advisor."},
            {"role": "user", "content": f"Use this context: {context}\n\nQuestion: {user_input}"}
        ],
        # messages=[
        #     {"role": "system", "content": (
        #         "You are a flooring advisor. If the user asks for suggestions, respond only with product names, models, or descriptions "
        #         "extracted from the brochures. Prioritize concise product listings with supporting descriptions from context. "
        #         "Avoid generic product advice unless context is insufficient."
        #     )},
        #     {"role": "user", "content": f"Use this context: {context}\n\nQuestion: {user_input}"}
        # ],
        max_tokens=1024
    )

    return chat_response.choices[0].message.content