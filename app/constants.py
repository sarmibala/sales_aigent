# app/constants.py

from app.models import IndexName

# Map UI/index to DB classification
INDEX_TO_DB_CLASSIFICATION = {
    IndexName.soft_surface.value: "SoftSurface",
    IndexName.hard_surface.value: "HardSurface",
}

INDEX_TO_JSON_FILE = {
    IndexName.all_products: "data/cache/cached_all_products.json",
    IndexName.soft_surface: "data/cache/cached_soft_surface_products.json",
    IndexName.hard_surface: "data/cache/cached_hard_surface_products.json"
}

ALLOWED_FILTER_FIELDS = [
    "collection_name",
    "sku",
    "style_number",
    "style_name",
    "dye_method",
    "dye_method_description",
    "surface_finish_description",
    "pattern_type",
    "pattern_scale",
    "budget_category",
    "stain_resistance",
    "product_group",
    "product_subgroup",
    "fiber_content_description",
    "producttype",
    "primarymarket",
    "segment",
    "stylewarranty1",
    "construction_category",
    "overview",
    "totalrecycledcontent",
    "embodied_carbon",
    "beyond_carbon_neutral",
    "installationmethod",
    "environmentalproductdeclaration",
    "carbon_handprint",
    "color_code",
    "marketing_color_name",
    "color_name",
    "size",
    "size_description",
    "backing_code"
    "backing_description",
    "introduction_date",
    "quickship",
    "finished_pile_thickness",
    "online_sample_available",
    "tarr",
    "tvoc_range",
    "product_family",
    "product_classification",
    "width_ft",
    "primary_backing",
    "sqft_per_carton",
    "pounds_per_carton",
    "color_family",
    "max_rollsize",
    "pieces_per_carton",
    "construction",
    "total_weight",
    "installation_pattern",
]