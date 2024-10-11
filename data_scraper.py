from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
import time

chrome_options = Options()
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors')

# Initialize WebDriver with options and service
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# URL of the page containing the grid
url = 'https://www.a101.com.tr/kapida/sut-urunleri-kahvaltilik/'
driver.get(url)
time.sleep(2)

# Scroll to load all products
scroll_pause_time = 2
last_height = driver.execute_script("return document.body.scrollHeight")

while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(scroll_pause_time)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

# Locate the grid containing the links
grid = driver.find_element(By.XPATH, "//div[contains(@class, 'grid grid-cols-3 justify-items-center')]")
links = grid.find_elements(By.XPATH, ".//a[@href]")
hrefs = [link.get_attribute('href') for link in links]

# List to store element information
elements_info = []

# Function to extract element information
def extract_element_info():
    try:
        # Extract the product image URL
        image_element = driver.find_element(By.XPATH, "//img[@alt]")
        image_url = image_element.get_attribute('src')

        # Extract product name
        product_name_element = driver.find_element(By.XPATH, "//h1[@class='text-2xl mb-2 font-normal mt-0 w-full']")
        product_name = product_name_element.text

        # Extract product code
        product_code_element = driver.find_element(By.XPATH, "//div[@class='text-sm text-brand-gray-secondary']")
        product_code = product_code_element.text.split(': ')[1]

        from selenium.common.exceptions import NoSuchElementException
        
        # Extract current price
        try:
            current_price_element = driver.find_element(By.XPATH, "//div[@class='text-2xl text-[#EA242A]']")
        except NoSuchElementException:
            current_price_element = driver.find_element(By.XPATH, "//div[@class='text-2xl text-[#333]']")
        current_price = current_price_element.text.strip()
        
        # Extract old price (nullable)
        try:
            old_price_element = driver.find_element(By.XPATH, "//div[@class='text-base text-[#333] line-through']")
            old_price = old_price_element.text.strip()
        except NoSuchElementException:
            old_price = "-"

        # Extract description
        description_element = driver.find_element(By.XPATH, "//div[@class='pt-4  mt-4 text-sm font-light  block']")
        description = description_element.text.strip()

        # Append extracted information to the list
        elements_info.append({
            'Resim': image_url,
            'Ürün Adı': product_name,
            'Ürün Kodu': product_code,
            'Son Fiyat': current_price,
            'Eski Fiyat': old_price,
            'Açıklama': description,
            'Kategori': 'Süt Ürünleri ve Kahvaltılıklar',
            'Kaynak': driver.current_url,
            'Tarih': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        })
    except Exception as e:
        print(f"Element not found: {e}")

# # Visit each link and extract specified elements
# for href in hrefs:
#     driver.get(href)
#     time.sleep(2)  # Wait for page to load
#     extract_element_info()

# Visit each link and extract specified elements
for index, href in enumerate(hrefs):
    # if index >= 5:
    #     break
    print(f"Processing {index + 1}/{len(hrefs)}: {href}")
    driver.get(href)
    time.sleep(2)  # Wait for page to load
    extract_element_info()
    print(f"Finished processing {index + 1}/{len(hrefs)}")

# Create a DataFrame from the extracted information
df = pd.DataFrame(elements_info)

# Save the DataFrame to a CSV file with UTF-8 encoding
df.to_csv('elements_info.csv', index=False, encoding='utf-8-sig')

driver.quit()  # Close the browser
