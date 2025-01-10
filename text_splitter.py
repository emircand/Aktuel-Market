import pandas as pd
import sys
import os
import json
import re

# Get the file name from the command-line arguments
if len(sys.argv) < 2:
    print("Usage: python text_splitter.py <input_file>")
    sys.exit(1)

input_file = sys.argv[1]

# Load the data from the CSV file
df = pd.read_csv(input_file)

# Ensure 'Açıklama' column exists
if 'Açıklama' not in df.columns:
    df['Açıklama'] = ""

# Fill NaN values with empty strings in the 'Açıklama' column
df['Açıklama'] = df['Açıklama'].fillna('')

# Function to extract quantity (Adet) from 'Ürün Adı'
def extract_adet(product_name):
    if pd.isna(product_name):
        return None
    match = re.search(r'(\d+)\s*[\'\']?[lL][iİıIuUüÜ]', product_name, re.IGNORECASE)
    if match:
        return match.group(1)[::-1]
    match = re.search(r'x\s*(\d+)', product_name, re.IGNORECASE)
    if match:
        return match.group(1)[::-1]
    return None

# Function to extract unit and amount (Birim and Miktar) from 'Ürün Adı'
def extract_birim_miktar(product_name):
    if pd.isna(product_name):
        return None, None
    reversed_name = product_name[::-1]
    match = re.search(r'([a-zA-Z]+)\s*([\d,\.]+)', reversed_name)
    if match:
        return match.group(1)[::-1], match.group(2)[::-1].replace(',', '.')
    match = re.search(r'([a-zA-Z]+)\s*([\d,\.]+)\s*x', reversed_name, re.IGNORECASE)
    if match:
        return match.group(1)[::-1], match.group(2)[::-1].replace(',', '.')
    return None, None

# Function to process JSON content and extract sections
def process_json_content(json_content, section_names):
    # Initialize all sections with default value
    sections = {name: "-" for name in section_names}
    
    for item in json_content:
        tab_name = item.get("Tab Name", "").strip().lower()
        content = item.get("Content", "-")
        
        # Normalize section names for matching
        normalized_section_names = [name.strip().lower() for name in section_names]
        
        if tab_name in normalized_section_names:
            matched_section = section_names[normalized_section_names.index(tab_name)]
            sections[matched_section] = content
    
    return sections

# Apply the functions to the 'Ürün Adı' column to create 'Adet', 'Birim', and 'Miktar'
df['Adet'] = df['Ürün Adı'].apply(lambda x: extract_adet(x) if extract_adet(x) is not None else '1')
df['Birim'], df['Miktar'] = zip(*df['Ürün Adı'].apply(extract_birim_miktar))

# Function to validate JSON
def is_valid_json(string):
    try:
        json.loads(string)
        return True
    except json.JSONDecodeError:
        return False

# Process JSON content in 'Açıklama'
if 'Açıklamalar' in df.columns:
    keywords = ["Saklama Koşulları", "İçindekiler", "Besin Değerleri", "Alerjen Uyarısı", "Kullanım Önerisi", "Ürün Bilgileri", "İade Koşulları"]
    
    def safe_process_json_content(x):
        if x and is_valid_json(x):
            return process_json_content(json.loads(x), keywords)
        return {name: "-" for name in keywords}
    
    # Apply processing with debugging
    sections_df = df['Açıklamalar'].apply(safe_process_json_content)
    sections_df = pd.DataFrame(sections_df.tolist(), index=df.index)
    
    # Merge results
    df = pd.concat([df, sections_df], axis=1)
    df.drop(columns=['Açıklamalar'], inplace=True)
    df.drop(columns=['Açıklama'], inplace=True)
else:
    print("Column 'Açıklamalar' not found or empty.")

# Reorder columns to place 'Adet', 'Birim', and 'Miktar' next to 'Ürün Adı'
columns = list(df.columns)
urun_adi_index = columns.index('Ürün Adı')
new_columns_order = columns[:urun_adi_index + 1] + ['Adet', 'Birim', 'Miktar'] + [col for col in columns[urun_adi_index + 1:] if col not in ['Adet', 'Birim', 'Miktar']]
df = df[new_columns_order]

# Remove duplicated rows
df = df.drop_duplicates()

# Save the updated dataframe to a new CSV file
output_file = input_file.replace('.csv', '_updated.csv')
df.to_csv(output_file, index=False, encoding='utf-8-sig')

print(f"Results saved to {output_file}")