# app/bulk_embed.py

import pandas as pd
import requests
import os
import urllib.parse
from io import BytesIO
from dotenv import load_dotenv
from app.embedding import process_pdf
load_dotenv()

def get_excel_download_url(google_sheet_url: str) -> str:
    try:
        # Extract sheet ID from the URL
        if "/d/" in google_sheet_url:
            sheet_id = google_sheet_url.split("/d/")[1].split("/")[0]
            export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
            return export_url
        else:
            raise ValueError("Invalid Google Sheets URL format")
    except Exception as e:
        raise ValueError(f"Error parsing URL: {e}")


def process_bulk_embedding(excel_url: str, index_name: str):
    try:
        PYTHON_APP_BASE_URL = os.getenv("PYTHON_APP_BASE_URL")
        download_url = get_excel_download_url(excel_url)
        print(download_url)
        
        # Download Excel content from URL
        response = requests.get(download_url)
        if response.status_code != 200:
            return {"status": "error", "message": f"Failed to download Excel file: {response.status_code}"}

        df = pd.read_excel(BytesIO(response.content))

        # Process all pdf files (Extract, clean, sort, and slice the URLs)
        distinct_brochures = df['CollectionBrochure'].dropna().drop_duplicates().tolist()
        
        # # Process First 5 pdf files only (Extract, clean, sort, and slice the URLs)
        # start, limit = 0, 5
        # distinct_brochures = (df['CollectionBrochure'].dropna().drop_duplicates().sort_values().tolist())[start:start+limit]

        print(f"Found {len(distinct_brochures)} unique brochure URLs")

        results = []

        for url in distinct_brochures:
            try:
                result = process_pdf(url, index_name)
                results.append({"url": url, "result": result})
            except Exception as e:
                results.append({"url": url, "error": str(e)
                })

        return {"processed": len(results), "results": results}

    except Exception as e:
        return {"status": "error", "message": str(e)}