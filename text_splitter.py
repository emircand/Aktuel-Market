import pandas as pd
import re
import sys

# Get the file name from the command-line arguments
if len(sys.argv) < 2:
    print("Usage: python text_splitter.py <input_file>")
    sys.exit(1)

input_file = sys.argv[1]

# Load the data from the CSV file
df = pd.read_csv(input_file)

# Function to extract quantity (Adet) from 'Ürün Adı'
def extract_adet(product_name):
    reversed_name = product_name[::-1]
    match = re.search(r'[lL][iİıIuUüÜ][\'’]?\s*(\d+)', reversed_name, re.IGNORECASE)
    if match:
        return match.group(1)[::-1]  # Return the quantity found, reversed back
    match = re.search(r'x\s*(\d+)', reversed_name, re.IGNORECASE)
    if match:
        return match.group(1)[::-1]  # Return the quantity found before 'x', reversed back
    return None  # Return None if no quantity is found

# Function to extract unit and amount (Birim and Miktar) from 'Ürün Adı'
def extract_birim_miktar(product_name):
    reversed_name = product_name[::-1]
    match = re.search(r'([a-zA-Z]+)\s*(\d+)', reversed_name)
    if match:
        return match.group(1)[::-1], match.group(2)[::-1]  # Return the unit and amount found, reversed back
    match = re.search(r'([a-zA-Z]+)\s*(\d+)\s*x', reversed_name, re.IGNORECASE)
    if match:
        return match.group(1)[::-1], match.group(2)[::-1]  # Return the unit and amount found after 'x', reversed back
    return None, None  # Return None if no unit and amount are found

# Function to extract specific sections from 'Açıklama' until the next keyword occurs
def extract_sections(text, keywords):
    sections = {keyword: None for keyword in keywords}
    pattern = re.compile(r'(' + '|'.join(re.escape(keyword) for keyword in keywords) + r')\s*(?:\:)?\s*(.*?)(?=' + '|'.join(r'\s*' + re.escape(keyword) + r'\s*(?:\:)?' for keyword in keywords) + r'|$)', re.DOTALL)
    matches = pattern.findall(text)
    for match in matches:
        keyword, content = match
        sections[keyword.strip()] = content.strip()
    return sections

# Apply the functions to the 'Ürün Adı' column to create 'Adet', 'Birim', and 'Miktar'
df['Adet'] = df['Ürün Adı'].apply(extract_adet)
df['Birim'], df['Miktar'] = zip(*df['Ürün Adı'].apply(extract_birim_miktar))

# Check if 'Açıklama' column exists
if 'Açıklama' in df.columns:
    # Extract specific sections from 'Açıklama'
    keywords = ["Saklama Koşulları", "İçindekiler", "Besin Değerleri", "Alerjen Uyarısı", "Kullanım Önerisi"]
    sections_df = df['Açıklama'].apply(lambda x: extract_sections(x, keywords))
    sections_df = pd.DataFrame(sections_df.tolist(), index=df.index)
    
    # Merge the sections DataFrame with the original DataFrame
    df = pd.concat([df, sections_df], axis=1)
else:
    print("Column 'Açıklama' not found in the input file.")

# Reorder columns to place 'Adet', 'Birim', and 'Miktar' next to 'Ürün Adı'
columns = list(df.columns)
urun_adi_index = columns.index('Ürün Adı')
new_columns_order = columns[:urun_adi_index + 1] + ['Adet', 'Birim', 'Miktar'] + columns[urun_adi_index + 1:]
df = df[new_columns_order]

# Remove duplicated rows
df = df.drop_duplicates()

# Save the updated dataframe to a new CSV file
output_file = input_file.replace('.csv', '_updated.csv')
df.to_csv(output_file, index=False, encoding='utf-8-sig')

# Optionally, print the first few rows to verify
print(df.head())