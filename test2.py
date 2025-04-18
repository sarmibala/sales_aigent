import pandas as pd

# === Configuration ===
excel_path = 'data\MohawkGroup_Product_SpecSheet.xlsx' 
excluded_columns = [
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

# === Load Excel ===
df = pd.read_excel(excel_path)

# Step 1: Excluded columns 
df = df.drop(columns=[col for col in excluded_columns if col in df.columns])

# Step 2: Normalize column names
df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

# Step 3: Remove columns with .1, .2 suffixes (assumed duplicates)
# Keep only first occurrence of each base column name
seen = set()
cleaned_columns = []
drop_indices = []

for i, col in enumerate(df.columns):
    base_col = col.split(".")[0]
    if base_col not in seen:
        cleaned_columns.append(base_col)
        seen.add(base_col)
    else:
        drop_indices.append(i)  # mark duplicate for dropping

# Drop duplicate columns
df = df.drop(df.columns[drop_indices], axis=1)

# Reassign cleaned column names
df.columns = cleaned_columns

# === Infer field types and nullability ===
def infer_field_type(series):
    if pd.api.types.is_integer_dtype(series.dropna()):
        return "Integer"
    elif pd.api.types.is_float_dtype(series.dropna()):
        return "Float"
    else:
        return "String"

# === SQLAlchemy Model ===
sqlalchemy_fields = []
for col in df.columns:
    col_type = infer_field_type(df[col])
    # sqlalchemy_fields.append(f"    {col} = Column({col_type}, nullable=True)")
    if col == "overview":
        sqlalchemy_fields.append(f"    {col} = Column(Text, nullable=True)")
    else:
        sqlalchemy_fields.append(f"    {col} = Column({col_type}, nullable=True)")

sqlalchemy_model = f"""from sqlalchemy import Column, Integer, String, Float, Text
from app.db.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
{chr(10).join(sqlalchemy_fields)}
"""

# === Pydantic Schema ===
from typing import Optional

pydantic_fields = []
for col in df.columns:
    col_type = infer_field_type(df[col])
    py_type = "int" if col_type == "Integer" else "float" if col_type == "Float" else "str"
    pydantic_fields.append(f"    {col}: Optional[{py_type}] = None")

pydantic_schema = f"""from pydantic import BaseModel
from typing import Optional

class ProductSchema(BaseModel):
{chr(10).join(pydantic_fields)}

    class Config:
        orm_mode = True
"""

# === Output to file or console ===
with open("generated_product_model.py", "w") as f:
    f.write(sqlalchemy_model)
    f.write("\n\n")
    f.write(pydantic_schema)

print("✅ Models generated in generated_product_model.py")