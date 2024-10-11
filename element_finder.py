from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time

chrome_options = Options()
chrome_options.add_argument('--ignore-certificate-errors')  # Ignore SSL certificate errors
chrome_options.add_argument('--ignore-ssl-errors')  # Also ignore SSL errors

# Initialize WebDriver with options and service
service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(service=service, options=chrome_options)

# URL of the A101 product page
url = 'https://www.a101.com.tr/kapida/sut-urunleri-kahvaltilik/birsah-yagli-sut-1-l_p-12000001'
driver.get(url)
time.sleep(2)  # Wait for page to load

# JavaScript to capture click events and log detailed element information
script = """
document.addEventListener('click', function(event) {
    var element = event.target;
    var elementInfo = {
        tagName: element.tagName,
        className: element.className,
        id: element.id,
        textContent: element.textContent.trim()
    };
    window.elementInfo = elementInfo;
});
"""

# Execute the script in the browser
driver.execute_script(script)

# Open a file to log element information
with open('clicked_elements_info.txt', 'w', encoding='utf-8') as file:
    try:
        while True:
            # Get the element information from the browser
            element_info = driver.execute_script("return window.elementInfo;")
            if element_info:
                # Format the element information as a string
                element_info_str = f"Tag: {element_info['tagName']}, Class: {element_info['className']}, ID: {element_info['id']}, Text: {element_info['textContent']}\n"
                file.write(element_info_str)
                file.flush()  # Ensure the data is written to the file
                driver.execute_script("window.elementInfo = null;")  # Reset the element information
            time.sleep(1)  # Adjust the sleep time as needed
    except KeyboardInterrupt:
        print("Stopping the program...")

driver.quit()  # Close the browser