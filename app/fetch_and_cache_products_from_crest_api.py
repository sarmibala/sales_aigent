import os
import json
import httpx
from fastapi.responses import JSONResponse

async def fetch_and_cache_products_from_crest_api():
    timeout = httpx.Timeout(30.0)
    MOHAWK_PRODUCTS_CREST_API_BASE_URL = os.getenv("MOHAWK_PRODUCTS_CREST_API_BASE_URL")

    SOFT_SURFACE_URL = f'{MOHAWK_PRODUCTS_CREST_API_BASE_URL}api/GetProductsByBrandCodeSite/MohawkGroup/SoftSurface'
    HARD_SURFACE_URL = f'{MOHAWK_PRODUCTS_CREST_API_BASE_URL}api/GetProductsByBrandCodeSite/MohawkGroup/HardSurface'

    OUTPUT_DIR = "data/cache"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            soft_res = await client.get(SOFT_SURFACE_URL)
            hard_res = await client.get(HARD_SURFACE_URL)

            soft_res.raise_for_status()
            hard_res.raise_for_status()

            soft_data = soft_res.json()
            hard_data = hard_res.json()
            combined_data = soft_data + hard_data

            # Save to files
            with open(os.path.join(OUTPUT_DIR, "cached_soft_surface_products.json"), "w") as sf:
                json.dump(soft_data, sf, indent=2)

            with open(os.path.join(OUTPUT_DIR, "cached_hard_surface_products.json"), "w") as hf:
                json.dump(hard_data, hf, indent=2)

            with open(os.path.join(OUTPUT_DIR, "cached_all_products.json"), "w") as af:
                json.dump(combined_data, af, indent=2)

            return JSONResponse(content={
                "message": "Products fetched and cached successfully.",
                "soft_count": len(soft_data),
                "hard_count": len(hard_data),
                "total": len(combined_data)
            })

        except httpx.RequestError as e:
            return JSONResponse(status_code=500, content={"error": f"Request failed: {str(e)}"})

        except Exception as e:
            return JSONResponse(status_code=500, content={"error": f"Unexpected error: {str(e)}"})