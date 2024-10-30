from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
import time

# Load URLs from file
with open('migros_category_href.txt', 'r') as file:
    urls = [line.strip() for line in file.readlines()]

# Initialize WebDriver with options and service
chrome_options = Options()
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors')
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# List to store element information
elements_info = []

# Function to extract element information with category name
def extract_element_info(category_name):
    try:
        # Extract the product image URL
        image_element = driver.find_element(By.XPATH, "//img[@alt]")
        image_url = image_element.get_attribute('src')

        # Extract product name
        product_name_element = driver.find_element(By.XPATH, "//h3[@class='text-color-black']")
        product_name = product_name_element.text

        # # Extract product code
        # product_code_element = driver.find_element(By.XPATH, "//p[@class='ProductMainInfoArea_productCode__smjcO']")
        # product_code = product_code_element.text.strip()

        # Extract current price
        try:
            current_price_element = driver.find_element(By.XPATH, "//span[@class='single-price-amount']")
        except NoSuchElementException:
            current_price_element = driver.find_element(By.XPATH, "//div[@class='price-new subtitle-1 ng-star-inserted']")
        current_price = current_price_element.text.strip()
        
        # Extract old price (nullable)
        try:
            old_price_element = driver.find_element(By.XPATH, "//div[@class='price mat-caption-bold']")
            old_price = old_price_element.text.strip()
        except NoSuchElementException:
            old_price = "-"
        # Extract description
        description_element = driver.find_element(By.XPATH, "//div[@class='product-description desktop-only ng-star-inserted']")
        description = description_element.text.strip()

        # Append extracted information to the list
        elements_info.append({
            'Resim': image_url,
            'Ürün Adı': product_name,
            # 'Ürün Kodu': product_code,
            'Son Fiyat': current_price,
            'Eski Fiyat': old_price,
            'Açıklama': description,
            'Kategori': category_name,
            'Kaynak': driver.current_url,
            'Tarih': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        })
    except Exception as e:
        print(f"Element not found: {e}")

# Extract category name from URL
def extract_category_name(url):
    # Find the part of the URL before "-c-"
    if "-c-" in url:
        category_name = url.split("-c-")[0]
    else:
        category_name = url

    # Assuming the category is the last part of the URL before "-c-"
    category_name = category_name.rstrip('/').split('/')[-1]
    
    # Replace dashes with spaces and capitalize words
    category_name = category_name.replace('-', ' ').title()
    
    return category_name

# Loop through each URL from the file and scrape data
for index, url in enumerate(urls):
    print(f"Processing {index + 1}/{len(urls)}: {url}")
    driver.get(url)
    time.sleep(2)  # Wait for page to load
    
    # Extract category name from URL
    category_name = extract_category_name(url)
    
    # Scroll to load all products if necessary
    scroll_pause_time = 2
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Class name for grids containing product information
    grid_class = 'mdc-layout-grid__cell--span-2-desktop mdc-layout-grid__cell--span-4-tablet mdc-layout-grid__cell--span-2-phone ng-star-inserted'
    
    # Try locating all grids on the page with the given class
    try:
        grids = driver.find_elements(By.XPATH, "//div[@class='mdc-layout-grid__inner product-cards list ng-star-inserted']")
        print(f"Found {len(grids)} grids with the specified class.")

        hrefs = []
        # Iterate over each grid and collect links only if visible
        for grid in grids:
            links = grid.find_elements(By.XPATH, ".//a[@href]")
            for link in links:
                if link.is_displayed():  # Only process visible links
                    hrefs.append(link.get_attribute('href'))

    except NoSuchElementException:
        print("No grid found with the specified class.")
    
    # Visit each product link and extract the information
    for href_index, href in enumerate(hrefs):
        print(f"Processing product {href_index + 1}/{len(hrefs)} in category {category_name}: {href}")
        driver.get(href)
        time.sleep(2)  # Wait for page to load
        extract_element_info(category_name)

    print(f"Finished processing category {category_name}.")

# Create a DataFrame from the extracted information
df = pd.DataFrame(elements_info)

# Save the DataFrame to a CSV file with UTF-8 encoding
df.to_csv('migros_elements_info.csv', index=False, encoding='utf-8-sig')

driver.quit()  # Close the browser
