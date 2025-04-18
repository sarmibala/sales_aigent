import pandas as pd
from io import BytesIO
from sqlalchemy.orm import Session
from app.db.models.product import Product
from app.schemas.product import ProductSchema
from sqlalchemy import Column, Integer, String, Float, Text

EXCLUDED_COLUMNS = [
    'display_product_category', 'company', 'global_availablity',
    'SellingStyleBulletContent7', 'SellingStyleBulletContent8', 'SellingStyleBulletContent9',
    'SlipResistance', 'Hardness', 'style_weight',
    'RHLimit', 'Underlayment', 'Abrasion_Resistance',
    'Grade_Level', 'Antimicrobial_Antifungal_Resistance_Test', 'Wear_Resistance',
    'Core', 'Carb2Compliant', 'LaceyActCompliant',
    'ADA_compliance', 'IIC_sound_rating', 'thickness_swell',
    'large_ball_impact_resistance', 'small_ball_impact_resistance', 'dimensional_tolerance',
    'chair_resistance', 'surface_bond', 'rolling_load_limit',
    'electrostatic_propensity', 'Trim_And_Moldings', 'spread_rate',
    'drop_date', 'quick_ship_instock', 'quick_ship_regular',
    'cdph_compliant', 'green_tag', 'pre_consumer_recyled_content',
    'post_consumer_recyled_content', 'renewable_content', 'location_city_state',
    'locataion_of_manufacture', 'materials_recyclable', 'map_price',
    'master_color_number', 'master_color_name', 'salesman_authreq_flag',
    'private_label_product', 'accessory_flag', 'identifier',
    'rolls_only', 'pitch', 'density',
    'declare_label', 'env_product_declaration', 'ca_prop65_warning',
    'ca_prop65_warning_detail', 'Accessories', 'TDS',
    'SalesSheet', 'SDS'
]

def create_product(db: Session, product_data: ProductSchema):
    db_product = Product(**product_data.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def get_all_products(db: Session):
    return db.query(Product).all()

def safe_cast(value, dtype):
    try:
        return dtype(value)
    except (ValueError, TypeError):
        return None

async def upsert_products_from_excel(file, db: Session):
    content = await file.read()
    df = pd.read_excel(BytesIO(content), dtype=str)
    df = df.where(pd.notnull(df), None) 

    # Step 1: Drop excluded columns
    df = df.drop(columns=[col for col in EXCLUDED_COLUMNS if col in df.columns])

    # Step 2: Normalize column names
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    # Step 3: Deduplicate columns (remove .1, .2 suffixes)
    seen = set()
    cleaned_columns, drop_indices = [], []
    for i, col in enumerate(df.columns):
        base_col = col.split(".")[0]
        if base_col not in seen:
            cleaned_columns.append(base_col)
            seen.add(base_col)
        else:
            drop_indices.append(i)
    df = df.drop(df.columns[drop_indices], axis=1)
    df.columns = cleaned_columns

    inserted, updated = 0, 0
    float_columns = [c.name for c in Product.__table__.columns if isinstance(c.type, Float)]

    for row in df.to_dict(orient="records"):
        # print(f'Row ==> {row}')
        for col in float_columns:
            row[col] = safe_cast(row.get(col), float) if pd.notnull(row.get(col)) else None

        sku = row.get("sku")
        if not sku:
            continue

        existing = db.query(Product).filter(Product.sku == sku).first()
        if existing:
            for key, value in row.items():
                setattr(existing, key, value)
            updated += 1
        else:
            product = Product(**row)
            # print(f'product ==> {product.__dict__}')
            db.add(product)
            inserted += 1

    db.commit()
    return {"inserted": inserted, "updated": updated, "total": inserted + updated}