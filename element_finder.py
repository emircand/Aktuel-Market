import pandas as pd
import re

# Function to extract specific sections from 'Açıklama' until the next keyword occurs
def extract_sections(text, keywords):
    sections = {keyword: None for keyword in keywords}
    pattern = re.compile(r'(' + '|'.join(re.escape(keyword) for keyword in keywords) + r')\s*(?:\:)?\s*(.*?)(?=' + '|'.join(r'\s*' + re.escape(keyword) + r'\s*(?:\:)?' for keyword in keywords) + r'|$)', re.DOTALL)
    matches = pattern.findall(text)
    for match in matches:
        keyword, content = match
        sections[keyword.strip()] = content.strip()
    return sections

# Example text
text = """
A101 Kapıda’da sunulan Kavun 5 kg ağırlığında bir adet kavun olarak sunulur. Dışı kabuklu meyve, sulu yapısı ve aromatik tadı ile severek tüketilir. 
Genel Özellikler
Yaz meyvesi: Yazın yetişen ve yaz meyvesi olarak bilinen gıda maddesi
Çekirdekli Yapı: Orta kısmında yer alan ve kolay bir şekilde sıyrılan yapısı
Yüksek Lif: Yüksek lif kaynağı yapısı ile uzun süreli tokluk hissi etkisi
Uyarılar
Potasyum, sodyum, kalsiyum, magnezyum, fosfat ile likopen ve beta-karoten gibi bitkisel besinler içerir.
Saklama Koşulları
0° ila 5° C’de muhafaza edilmelidir.
Kullanım Tavsiyesi 
Dilimleyerek ve kabuğundan ayırarak servis edebilirsiniz. Öğün arası olarak karpuz ve peynir ile birlikte tüketebilirsiniz. Aynı zamanda yaz aylarında dondurma da yapabilirsiniz.
Gramaj stoktaki ürüne göre değişebilecek olup, teslim edilen ürün gramajına göre tahsilat yapılmaktadır.

Teslimat adresinize göre ürünün stok durumu değişebilir. Teslimat adresinizi ekledikten sonra ürün stok durumunu görüntüleyebilirsiniz.
"""

# Keywords to extract
keywords = ["Genel Özellikler", "Uyarılar", "Saklama Koşulları", "Kullanım Tavsiyesi"]

# Extract sections
sections = extract_sections(text, keywords)

# Print extracted sections
for keyword, content in sections.items():
    print(f"{keyword}: {content}")