from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
import time
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ScraperConfig:
    name: str
    url_file: str
    selectors: Dict[str, str]
    grid_class: str
    output_file: str

class WebScraper:
    def __init__(self, config: ScraperConfig):
        self.config = config
        self.elements_info = []
        self.driver = self._initialize_driver()
        
    def _initialize_driver(self) -> webdriver.Chrome:
        chrome_options = Options()
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)

    def extract_element_info(self, category_name: str) -> None:
        try:
            # Extract common elements using configured selectors
            image_element = self.driver.find_element(By.XPATH, self.config.selectors['image'])
            image_url = image_element.get_attribute('src')
            
            product_name_element = self.driver.find_element(By.XPATH, self.config.selectors['product_name'])
            product_name = product_name_element.text
            
            # Extract current price with fallback
            try:
                current_price_element = self.driver.find_element(By.XPATH, self.config.selectors['current_price'])
            except NoSuchElementException:
                current_price_element = self.driver.find_element(By.XPATH, self.config.selectors['current_price_fallback'])
            current_price = current_price_element.text.strip()
            
            # Extract optional elements
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
                        product_info[field] = value
                    except NoSuchElementException:
                        product_info[field] = "-"
            
            self.elements_info.append(product_info)
            
        except Exception as e:
            print(f"Element not found: {e}")

    def extract_category_name(self, url: str) -> str:
        category_name = url.rstrip('/').split('/')[-1]
        if "-c-" in url:
            category_name = url.split("-c-")[0].rstrip('/').split('/')[-1]
        return category_name.replace('-', ' ').title()

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

    def scrape(self) -> None:
        with open(self.config.url_file, 'r') as file:
            urls = [line.strip() for line in file.readlines()]

        for index, url in enumerate(urls):
            print(f"Processing {index + 1}/{len(urls)}: {url}")
            self.driver.get(url)
            time.sleep(2)
            
            category_name = self.extract_category_name(url)
            self.scroll_page()
            
            try:
                if self.config.name == "migros":
                    # Special handling for Migros
                    grids = self.driver.find_elements(By.XPATH, 
                        "//div[contains(@class, 'mdc-layout-grid__inner product-cards list ng-star-inserted')]")
                else:
                    grids = self.driver.find_elements(By.CLASS_NAME, self.config.grid_class)
                
                print(f"Found {len(grids)} grids")
                
                hrefs = []
                for grid in grids:
                    links = grid.find_elements(By.XPATH, ".//a[@href]")
                    hrefs.extend([link.get_attribute('href') for link in links if link.is_displayed()])
                
                for href_index, href in enumerate(hrefs):
                    print(f"Processing product {href_index + 1}/{len(hrefs)} in {category_name}")
                    self.driver.get(href)
                    time.sleep(2)
                    self.extract_element_info(category_name)
                    
            except NoSuchElementException:
                print("No grid found")
                
        self._save_results()
        self.driver.quit()

    def _save_results(self) -> None:
        df = pd.DataFrame(self.elements_info)
        df.to_csv(self.config.output_file, index=False, encoding='utf-8-sig')

# Store configurations
MIGROS_CONFIG = ScraperConfig(
    name="migros",
    url_file="migros_category_href.txt",
    selectors={
        'image': "//img[@alt]",
        'product_name': "//h3[@class='text-color-black']",
        'current_price': "//span[@class='single-price-amount']",
        'current_price_fallback': "//div[@class='price-new subtitle-1 ng-star-inserted']",
        'old_price': "//div[@class='price mat-caption-bold']",
        'description': "//div[@class='product-description desktop-only ng-star-inserted']"
    },
    grid_class="mdc-layout-grid__cell--span-2-desktop.mdc-layout-grid__cell--span-4-tablet.mdc-layout-grid__cell--span-2-phone.ng-star-inserted",
    output_file="migros_elements_info.csv"
)

SOK_CONFIG = ScraperConfig(
    name="sok",
    url_file="sok_category_href.txt", 
    selectors={
        'image': "//img[@alt]",
        'product_name': "//h1[@class='ProductMainInfoArea_productName__bKRVD']",
        'product_code': "//div[@class='ProductMainInfoArea_productCode__smjcO']",
        'current_price': "//span[@class='CPriceBox-module_discountedPrice__15Ffw']",
        'current_price_fallback': "//span[@class='CPriceBox-module_price__bYk-c']",
        'old_price': "//div[@class='CPriceBox-module_price__bYk-c']",
        'description': "//div[@class='ProductDescriptionTab_productDescriptionTab__CGdg7']"
    },
    grid_class="PLPProductListing_PLPCardParent__GC2qb",
    output_file="sok_elements_info.csv"
)



A101_CONFIG = ScraperConfig(
    name="a101",
    url_file="a101_category_href.txt",
    selectors={
        'image': "//img[@alt]",
        'product_name': "//h1[@class='text-2xl mb-2 font-normal mt-0 w-full']",
        'current_price': "//div[@class='text-2xl text-[#EA242A]']",
        'current_price_fallback': "//div[@class='text-2xl text-[#333]']",
        'product_code': "//div[@class='text-sm text-brand-gray-secondary']",
        'old_price': "//div[@class='text-base text-[#333] line-through']",
        'description': "//div[@class='pt-4  mt-4 text-sm font-light  block']"
    },
    grid_class="gap-2.grid.grid-cols-3.justify-items-center",
    output_file="a101_elements_info.csv"
)

# Usage example
scraper = WebScraper(MIGROS_CONFIG)
scraper.scrape()