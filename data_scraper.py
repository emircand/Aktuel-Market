import json
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from urllib.parse import urljoin, urlparse
from selenium.common.exceptions import InvalidArgumentException
import pandas as pd
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
import subprocess
import os

@dataclass
class ScraperConfig:
    name: str
    selectors: Dict[str, str]
    grid_class: str
    output_file: str

class WebScraper:
    def __init__(self, config: ScraperConfig, category_mapper: Dict[str, Dict[str, str]], browser: str):
        self.config = config
        self.category_mapper = category_mapper
        self.elements_info = []
        self.browser = browser  # Set browser from argument
        self.driver = self._initialize_driver()
        
    def _initialize_driver(self) -> webdriver.Chrome:
        if self.browser.lower() == 'chrome':
            chrome_options = ChromeOptions()
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            service = ChromeService(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=chrome_options)
        elif self.browser.lower() == 'firefox':
            firefox_options = FirefoxOptions()
            firefox_options.add_argument('--ignore-certificate-errors')
            firefox_options.add_argument('--ignore-ssl-errors')
            firefox_options.add_argument('--disable-web-security')
            firefox_options.add_argument('--allow-running-insecure-content')
            service = FirefoxService(GeckoDriverManager().install())
            return webdriver.Firefox(service=service, options=firefox_options)
        elif self.browser.lower() == 'edge':
            edge_options = EdgeOptions()
            edge_options.add_argument('--ignore-certificate-errors')
            edge_options.add_argument('--ignore-ssl-errors')
            edge_options.add_argument('--disable-web-security')
            edge_options.add_argument('--allow-running-insecure-content')
            service = EdgeService(EdgeChromiumDriverManager().install())
            return webdriver.Edge(service=service, options=edge_options)
        else:
            raise ValueError(f"Unsupported browser: {self.browser}")

    def extract_element_info(self, category_name: str) -> None:
        try:
            # Extract common elements using configured selectors
            image_element = self.driver.find_element(By.XPATH, self.config.selectors['image'])
            image_url = image_element.get_dom_attribute('src')
            
            product_name_element = self.driver.find_element(By.XPATH, self.config.selectors['product_name'])
            product_name = product_name_element.text
            
            # Extract current price with fallback
            try:
                current_price_element = self.driver.find_element(By.XPATH, self.config.selectors['current_price'])
            except NoSuchElementException:
                current_price_element = self.driver.find_element(By.XPATH, self.config.selectors['current_price_fallback'])
            current_price = current_price_element.text.strip()
            
            product_info = {
                'Resim': image_url,
                'Ürün Adı': product_name,
                'Son Fiyat': current_price,
                'Kategori': category_name,
                'Kaynak': self.driver.current_url,
                'Tarih': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            }

            # Add optional fields if configured
            for field, selector in self.config.selectors.items():
                if field not in ['image', 'product_name', 'current_price', 'current_price_fallback']:
                    try:
                        element = self.driver.find_element(By.XPATH, selector)
                        if field == 'product_code':
                            value = element.text.split(': ')[1] if ': ' in element.text else element.text
                        else:
                            value = element.text.strip()
                        if self.config.name == 'migros':
                            product_info['Ürün Kodu'] = "-"
                        else:
                            product_info['Ürün Kodu'] = value
                    except NoSuchElementException:
                        product_info['Ürün Kodu'] = "-"

            # Extract old price if available
            if 'old_price' in self.config.selectors:
                try:
                    old_price_element = self.driver.find_element(By.XPATH, self.config.selectors['old_price'])
                    old_price = old_price_element.text.strip()
                    product_info['Eski Fiyat'] = old_price
                except NoSuchElementException:
                    product_info['Eski Fiyat'] = "-"

            # Extract description if available
            if 'description' in self.config.selectors:
                try:
                    description_element = self.driver.find_element(By.XPATH, self.config.selectors['description'])
                    description = description_element.text.strip()
                    product_info['Açıklama'] = description
                except NoSuchElementException:
                    product_info['Açıklama'] = "-"

            self.elements_info.append(product_info)
            
        except Exception as e:
            print(f"Element not found: {e}")

    def scroll_page(self) -> None:
        scroll_pause_time = 2
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause_time)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def scrape_category(self, category_data: Dict[str, Dict[str, str]], category_name: str) -> None:
        if 'urls' not in category_data or self.config.name not in category_data['urls']:
            print(f"Store '{self.config.name}' not found for category '{category_name}'.")
            return

        base_url = category_data['urls'][self.config.name]
        print(f"Processing category '{category_name}' with URL: {base_url}")
        
        try:
            self.driver.get(base_url)
            time.sleep(2)
            
            self.scroll_page()
            
            try:
                if self.config.name == "migros":
                    grids = self.driver.find_elements(By.XPATH, 
                        "//div[contains(@class, 'mdc-layout-grid__inner product-cards list ng-star-inserted')]")
                else:
                    grids = self.driver.find_elements(By.CLASS_NAME, self.config.grid_class)
                
                print(f"Found {len(grids)} grids")
                
                hrefs = []
                for grid in grids:
                    if self.config.name == "migros":
                        links = grid.find_elements(By.XPATH, ".//a[@href and @id='product-name']")
                    else:
                        links = grid.find_elements(By.XPATH, ".//a[@href]")
                    
                    # Ensure URLs are absolute and valid
                    for link in links:
                        if link.is_displayed():
                            href = link.get_dom_attribute('href')
                            if href:
                                # Convert relative URLs to absolute
                                absolute_url = urljoin(base_url, href)
                                # Validate URL
                                try:
                                    parsed = urlparse(absolute_url)
                                    if all([parsed.scheme, parsed.netloc]):
                                        hrefs.append(absolute_url)
                                except Exception as e:
                                    print(f"Invalid URL: {absolute_url}, Error: {e}")
                
                print(f"Found {len(hrefs)} valid product URLs")
                
                for href_index, href in enumerate(hrefs):
                    try:
                        print(f"Processing product {href_index + 1}/{len(hrefs)} in {category_name}")
                        print(f"URL: {href}")
                        self.driver.get(href)
                        time.sleep(2)
                        self.extract_element_info(category_name)
                    except InvalidArgumentException as e:
                        print(f"Invalid URL: {href}")
                        print(f"Error: {e}")
                        continue
                    except Exception as e:
                        print(f"Error processing {href}: {e}")
                        continue
                    
            except NoSuchElementException:
                print("No grid found")
                    
            self._save_results()
            
        except Exception as e:
            print(f"Error scraping category {category_name}: {e}")
        finally:
            self.driver.quit()

    def scrape(self, chosen_category: str, subcategory_path: Optional[List[str]] = None) -> None:
        def recursive_scrape(category_data, category_name):
            self.scrape_category(category_data, category_name)
            if 'subcategories' in category_data:
                for subcategory_name, subcategory_data in category_data['subcategories'].items():
                    print(f"Processing subcategory: {subcategory_name}")
                    recursive_scrape(subcategory_data, subcategory_name)

        if chosen_category not in self.category_mapper['categories']:
            print(f"Category '{chosen_category}' not found in category mapper.")
            return

        category_data = self.category_mapper['categories'][chosen_category]

        # Navigate through the subcategory path if provided
        if subcategory_path:
            for subcategory in subcategory_path:
                if 'subcategories' in category_data and subcategory in category_data['subcategories']:
                    category_data = category_data['subcategories'][subcategory]
                else:
                    print(f"Subcategory '{subcategory}' not found under category '{chosen_category}'.")
                    return

        recursive_scrape(category_data, chosen_category)

    def _save_results(self) -> None:
        timestamp = time.strftime('%Y%m%d_%H%M%S', time.localtime())
        output_directory = os.path.join("marketplace", self.config.name)
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        output_file_with_timestamp = os.path.join(output_directory, f"{self.config.output_file}_{timestamp}.csv")
        df = pd.DataFrame(self.elements_info)
        
        # Remove duplicated rows
        df = df.drop_duplicates()
        
        df.to_csv(output_file_with_timestamp, index=False, encoding='utf-8-sig')
        print(f"Results saved to {output_file_with_timestamp}")
        
        # Run text_splitter.py with the marketplace directory
        subprocess.run(["python", "text_splitter.py", output_file_with_timestamp, output_directory])

def load_config(file_path: str) -> ScraperConfig:
    with open(file_path, 'r') as file:
        config_data = json.load(file)
    return ScraperConfig(**config_data)

def load_category_mapper(file_path: str) -> Dict[str, Dict[str, str]]:
    with open(file_path, 'r') as file:
        return json.load(file)

def normalize_string(input_str: str) -> str:
    replacements = {
        'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u',
        'Ç': 'C', 'Ğ': 'G', 'İ': 'I', 'Ö': 'O', 'Ş': 'S', 'Ü': 'U'
    }
    for turkish_char, english_char in replacements.items():
        input_str = input_str.replace(turkish_char, english_char)
    return input_str.lower()

# Usage example
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python data_scraper.py <category> <marketplace> <browser> [<subcategory1> <subcategory2> ...]")
        sys.exit(1)
    
    category = sys.argv[1]
    marketplace = sys.argv[2]
    browser = sys.argv[3].lower()
    subcategory_path = [sub for sub in sys.argv[4:]] if len(sys.argv) > 4 else None

    config_file_path = f'{marketplace}_config.json'  # Config file path based on marketplace
    category_mapper_file_path = 'subcategory_mapper.json'  # Path to the category mapper file

    config = load_config(config_file_path)
    category_mapper = load_category_mapper(category_mapper_file_path)
    scraper = WebScraper(config, category_mapper, browser)  # Pass browser to WebScraper

    scraper.scrape(category, subcategory_path)