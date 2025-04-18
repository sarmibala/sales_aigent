import os
import pandas as pd

# Load the Excel file
file_path = 'data\MohawkGroup_Product_SpecSheet.xlsx' 
df = pd.read_excel(file_path)

print(f'Product Data Loaded')
print(f'Number of columns before drop: {df.shape[1]}')

# Specify the columns that we want to drop
columns_to_drop = ['display_product_category', 'company', 'global_availablity',
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
                   'SalesSheet', 'SDS'] 

# Drop the specified columns
df = df.drop(columns=columns_to_drop)

print(f'Number of columns after drop: {df.shape[1]}')
print(df.head())

# # Get distinct Collection names
# distinct_collections = df['collection_name'].dropna().drop_duplicates().tolist()

# # Sort the collection names alphabetically
# sorted_collections = sorted(distinct_collections)

# print(f"📘 Found {len(sorted_collections)} unique Collection names")
# for index, collection in enumerate(sorted_collections, start=1):
#     print(f'{index}. Collection name ==> {collection}')