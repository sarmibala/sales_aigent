# app/chat.py

import os
import json
import re
from openai import AzureOpenAI
from app.azure_search import search_similar_content
from azure.search.documents.models import VectorizedQuery
from app.db.database import get_db  # session management
from app.db.product_metadata import search_product_metadata
from app.models import IndexName
from app.constants import INDEX_TO_DB_CLASSIFICATION, INDEX_TO_JSON_FILE
from app.constants import ALLOWED_FILTER_FIELDS
from dotenv import load_dotenv
load_dotenv()

EMBEDDING_DIM = 3072

client = AzureOpenAI(
    api_version=os.getenv("AZURE_OPENAI_EMBEDDING_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY")
)

# Example function to generate document embedding
def generate_embeddings(text, model):
    # Generate embeddings for the provided text using the specified model
    embeddings_response = client.embeddings.create(model=model, input=text)
    # Extract the embedding data from the response
    embedding = embeddings_response.data[0].embedding
    return embedding

def load_cached_products(index_name):
    file_path = INDEX_TO_JSON_FILE.get(index_name)
    if not file_path or not os.path.exists(file_path):
        raise FileNotFoundError(f"Cache file for index '{index_name}' not found.")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_known_collections(index_name):
    data = load_cached_products(index_name)
    return {item.get("collectionName", "").strip() for item in data if item.get("collectionName")}

def get_known_styles(index_name):
    data = load_cached_products(index_name)
    return {item.get("styleName", "").strip() for item in data if item.get("styleName")}

def extract_structured_filters(user_query, index_name):
    # system_prompt = (
    #     "Extract key flooring product filters from the user query. "
    #     "Return them as a JSON object with possible keys: collection_name, style_name, color_code, marketing_color_name, construction, backing_description. "
    #     "Do not wrap the JSON inside markdown code block."
    # )

    known_collections = get_known_collections(index_name) 
    known_styles = get_known_styles(index_name)

    system_prompt = (
        "Extract key flooring product filters from the user query. "
        f"Allowed fields: {', '.join(ALLOWED_FILTER_FIELDS)}. "
        "Match terms to the most appropriate field. "
        f"If the value is in this list of collections: {known_collections}, assign it to `collection_name`. "
        f"If in this list of style names: {known_styles}, assign it to `style_name`. "
        "Return a valid JSON object, no markdown, no extra explanation."
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

    raw_keywords = response.choices[0].message.content.strip()
    print(f'raw_keywords ==> {raw_keywords}')

    try:
        # Strip code block formatting if present
        if raw_keywords.startswith("```"):
            raw_keywords = raw_keywords.split("```")[1].strip()

        filters = json.loads(raw_keywords)

        if "style_name" in filters:
            style = filters["style_name"]
            if style in known_collections:
                filters["collection_name"] = style
                del filters["style_name"]

        return {k: v for k, v in filters.items() if k in ALLOWED_FILTER_FIELDS and v}
    except Exception as e:
        print(f"[!] Failed to parse filter JSON: {e}")
        return {}

def enrich_with_api_data(product_rows, api_data):
    enriched_rows = []

    for row in product_rows:
        match = next(
            (item for item in api_data if
             item["sku"].strip() == (row.sku or "").strip()),
            None
        )

        enriched_rows.append({
            "style_name": row.style_name,
            "sku": row.sku,
            "collection_name": row.collection_name,
            "color": row.marketing_color_name,
            "construction": row.construction,
            "backing": row.backing_description,
            "producturl": match["producturl"] if match else None,
            "thumb_image": match["thumb_image"] if match else None
        })

    return enriched_rows

def chat_with_gpt(user_input, index_name):
    # Step 1: Embed query
    vector_query = VectorizedQuery(vector=generate_embeddings(user_input, os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")), k_nearest_neighbors=10, fields="embedding")
    print(f'User input ==> {user_input} & index_name ==> {index_name}')
    # print(f'query_vector ==> {vector_query}')

    # Step 2: Get unstructured brochure chunks
    top_chunks = search_similar_content(vector_query, index_name, top_k=10)
    print(f'Top chunks from Azure Search ==> {len(top_chunks)}')
    brochure_context = "\n\n".join(top_chunks)

    # Step 3: Get structured product rows
    db = next(get_db())
    filters = extract_structured_filters(user_input, index_name)

    # Inject classification for DB filtering
    if index_name == IndexName.all_products.value:
        filters["product_classification"] = list(INDEX_TO_DB_CLASSIFICATION.values())
    else:
        db_classification = INDEX_TO_DB_CLASSIFICATION.get(index_name)
        if db_classification:
            filters["product_classification"] = [db_classification]
        
    print(f"Structured Filters: {filters}")
    product_rows = search_product_metadata(db, filters, 10)
    print(f"product_rows: {product_rows}")

    if not product_rows:
        print(f'there is no product_rows')
        match = re.search(r"Collection:?\s*(.+?)(?:\n|$)", brochure_context, re.IGNORECASE)
        print(f"fallback match 1 : {match}")
        if match:
            print(f"fallback match 2 : {match}")
            inferred_collection = match.group(1).strip()
            print(f"🔁 Inferred collection from brochure: {inferred_collection}")
            fallback_filters = {
                "collection_name": inferred_collection,
                "product_classification": filters.get("product_classification", [])
            }
            print(f"fallback_filters: {fallback_filters}")
            product_rows = search_product_metadata(db, fallback_filters, 10)
            print(f"fallback product_rows: {product_rows}")

    api_data = load_cached_products(index_name)

    enriched = enrich_with_api_data(product_rows, api_data)

    print(f"enriched product_rows: {enriched}")

    # Build product section
    product_context = ""
    for p in enriched:
        product_context += (
            f"**Product**: {p['style_name']}  \n"
            f"**SKU**: {p['sku']}  \n"
            f"**Collection**: {p['collection_name']}  \n"
            f"**Color**: {p['color']}  \n"
            f"**Construction**: {p['construction']}  \n"
            f"**Backing**: {p['backing']}  \n"
            f"{'**URL**: ' + p['producturl'] if p['producturl'] else ''}  \n"
            f"{'![thumb](' + p['thumb_image'] + ')' if p['thumb_image'] else ''}  \n\n"
        )


    # product_context = ""
    # for product in product_rows:
    #     product_context += (
    #         f"Product: {product.style_name}, SKU: {product.sku}, Collection: {product.collection_name}, "
    #         f"Color: {product.marketing_color_name}, Construction: {product.construction}, "
    #         f"Backing: {product.backing_description}\n"
    #     )

    # Step 4: Combine into one prompt context
    full_context = f"== BROCHURE CONTEXT ==\n{brochure_context}\n\n== PRODUCT METADATA ==\n{product_context}"
    # print(f'full_context ==> {full_context}')

    # Optional: Trimming context if too long
    max_context_length = 1500
    if len(full_context.split()) > max_context_length:
        full_context = ' '.join(full_context.split()[:max_context_length])

    # GPT system prompt
    system_prompt = (
        "You are a helpful flooring advisor. "
        "Answer user questions using the provided context. "
        "Include key product details: name, SKU, collection, color, backing, construction, and product URL if available. "
        "Also show product thumbnails using Markdown `![image](url)` syntax. "
        "When responding, format your answer using Markdown. "
        "Use **bold**, *italics*, bullet points, numbered lists, and section headings (###) where appropriate. "
        "Your output will be displayed in a web UI that supports Markdown rendering via marked.js."
    )

    # Ask GPT
    chat_response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT_NAME"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Use this context: {full_context}\n\nQuestion: {user_input}"}
        ],
        max_tokens=1024
    )

    return chat_response.choices[0].message.content