import os
import numpy as np
from typing import Dict
from openai import AzureOpenAI
from app.azure_search import search_similar_content
from azure.search.documents.models import (
    QueryAnswerType,
    QueryCaptionType,
    QueryType,
    VectorizedQuery,
)
from app.db.database import get_db  # session management
from app.db.product_metadata import search_product_metadata

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

def extract_structured_filters(user_query: str) -> Dict[str, str]:
    system_prompt = (
        "Extract key flooring product filters from the user query. "
        "Return them as a JSON object with possible keys: collection_name, style_name, marketing_color_name, construction, backing_description. "
        "Do not wrap the JSON inside markdown code block."
    )

    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT_NAME"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Query: {user_query}"}
        ],
        temperature=0.2,
        max_tokens=100
    )

    import json
    raw_keywords = response.choices[0].message.content.strip()
    print(f'raw_keywords ==> {raw_keywords}')

    try:
        # Strip code block formatting if present
        if raw_keywords.startswith("```"):
            raw_keywords = raw_keywords.split("```")[1].strip()

        filters = json.loads(raw_keywords)
        return {k: v for k, v in filters.items() if v}
    except Exception as e:
        print(f"[!] Failed to parse filter JSON: {e}")
        return {}
    
# def extract_keywords(user_query: str) -> list[str]:
#     prompt = (
#         f"Extract key product attributes (like collection name, style name, color name and other key info) from this user query:\n"
#         f"Query: \"{user_query}\"\n"
#         f"Return them as a comma-separated list."
#     )

#     response = client.chat.completions.create(
#         model=os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT_NAME"),
#         messages=[
#             {"role": "system", "content": "You extract product attributes for flooring products."},
#             {"role": "user", "content": prompt}
#         ],
#         temperature=0.2,
#         max_tokens=100
#     )

#     raw_keywords = response.choices[0].message.content.strip()
#     return [kw.strip() for kw in raw_keywords.split(",") if kw.strip()]

# def extract_keywords(query: str) -> list[str]:
#     # Basic example: lowercase, remove punctuation, and split
#     query_clean = re.sub(r'[^\w\s]', '', query.lower())
#     return query_clean.split()

def chat_with_gpt(user_input: str):
    # Step 1: Embed query
    vector_query = VectorizedQuery(vector=generate_embeddings(user_input, os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")), k_nearest_neighbors=10, fields="embedding")
    print(f'User input ==> {user_input}')
    # print(f'query_vector ==> {vector_query}')

    # Step 2: Get unstructured brochure chunks
    top_chunks = search_similar_content(vector_query, top_k=10)
    print(f'Top chunks from Azure Search ==> {len(top_chunks)}')
    brochure_context = "\n\n".join(top_chunks)

    # Step 3: Get structured product rows
    db = next(get_db())
    filters = extract_structured_filters(user_input)
    print(f"🔎 Structured Filters: {filters}")
    product_rows = search_product_metadata(db, filters, 10)

    product_context = ""
    for product in product_rows:
        product_context += (
            f"Product: {product.style_name}, SKU: {product.sku}, Collection: {product.collection_name}, "
            f"Color: {product.marketing_color_name}, Construction: {product.construction}, "
            f"Backing: {product.backing_description}\n"
        )

    # Step 4: Combine into one prompt context
    full_context = f"== BROCHURE CONTEXT ==\n{brochure_context}\n\n== PRODUCT METADATA ==\n{product_context}"
    # print(f'full_context ==> {full_context}')

    # Optional: Trimming context if too long
    max_context_length = 1500
    if len(full_context.split()) > max_context_length:
        full_context = ' '.join(full_context.split()[:max_context_length])

    # Ask GPT
    chat_response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT_NAME"),
        messages=[
            {"role": "system", "content": "You are a flooring advisor."},
            {"role": "user", "content": f"Use this context: {full_context}\n\nQuestion: {user_input}"}
        ],
        # messages=[
        #     {"role": "system", "content": (
        #         "You are a flooring advisor. If the user asks for suggestions, respond only with product names, models, or descriptions "
        #         "extracted from the brochures. Prioritize concise product listings with supporting descriptions from context. "
        #         "Avoid generic product advice unless context is insufficient."
        #     )},
        #     {"role": "user", "content": f"Use this context: {full_context}\n\nQuestion: {user_input}"}
        # ],
        max_tokens=1024
    )

    return chat_response.choices[0].message.content