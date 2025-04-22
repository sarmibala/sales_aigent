import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from openai import AzureOpenAI
import numpy as np
from app.azure_search import create_vector_index, upload_documents_to_search
from dotenv import load_dotenv
load_dotenv()

EMBEDDING_DIM = 3072 # For text-embedding-3-large

client = AzureOpenAI(
    api_version=os.getenv("AZURE_OPENAI_EMBEDDING_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY")
)

def process_pdf(pdf_path: str):
    try:
        pdf_name = os.path.basename(pdf_path).replace(".pdf", "")
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = splitter.split_documents(documents)

        texts = [doc.page_content for doc in chunks if doc.page_content.strip()]
        metadata = [doc.metadata for doc in chunks if doc.page_content.strip()]

        if not texts:
            return {"status": "error", "message": "No valid text chunks to embed."}

        response = client.embeddings.create(
            input=texts,
            model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
        )

        vectors = []
        clean_metadata = []

        for i, item in enumerate(response.data):
            emb = getattr(item, "embedding", None)
            if emb and isinstance(emb, list) and len(emb) == EMBEDDING_DIM:
                vectors.append(np.array(emb, dtype=np.float32))
                clean_metadata.append(metadata[i] if i < len(metadata) else {})

        if not vectors:
            return {"status": "error", "message": "No valid embeddings were generated."}

        # create_vector_index(dim=EMBEDDING_DIM)
        upload_documents_to_search(pdf_name, texts, vectors, clean_metadata)

        return {"status": "embedded", "chunks": len(vectors)}

    except Exception as e:
        return {"status": "error", "message": str(e)}