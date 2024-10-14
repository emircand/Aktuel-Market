from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from selenium.common.exceptions import NoSuchElementException

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

# Scroll to load all products (if needed)
scroll_pause_time = 2
last_height = driver.execute_script("return document.body.scrollHeight")

while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(scroll_pause_time)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

# CSS selector to locate the anchor tags with the specified class names
css_selector = "a.bg-white.flex.items-center.rounded-full.overflow-hidden.cursor-pointer"

try:
    # Find all anchor tags <a> with the specified class names
    links = driver.find_elements(By.CSS_SELECTOR, css_selector)

    # Extract href attributes and print them
    hrefs = [link.get_attribute('href') for link in links if link.get_attribute('href')]

    # Print all the hrefs found
    print(f"Found {len(hrefs)} hrefs:")
    for href in hrefs:
        print(href)

except NoSuchElementException:
    print("Anchor tags with the specified class names not found.")
except Exception as e:
    print(f"An error occurred: {e}")

# Close the browser
driver.quit()