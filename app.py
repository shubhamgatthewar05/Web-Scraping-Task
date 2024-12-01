import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


def extract_metadata(driver, url):
    metadata = {}

    try:
        metadata['title'] = driver.title
    except Exception as e:
        metadata['title'] = None

    try:
        metadata['description'] = driver.fin_element(By.XPATH, "//meta[@name='description']").get_attribute('content')
    except Exception as e:
        metadata['description'] = None

    try:
        metadata['author'] = driver.find_element(By.XPATH, "//meta[@name = 'author]").get_attribute('content')
    except Exception as e:
        metadata['author'] = None
    
    try:
        metadata['keywords'] = driver.find_element(By.XPATH, "//meta[@name = 'keywords']").get_attribute('content')
    except Exception as e:
        metadata['keywords'] = None
    
    try:
        metadata['languageCode'] = driver.find_element(By.XPATH, "//html").get_attribute('lang')
    except Exception as e:
        metadata['languageCode'] = None
    
    metadata['canonicalUrl'] = driver.current_url

    return metadata


def capture_screenshot(driver):
    try:
        screenshot_path = 'screenshot.png'
        driver.save_screenshot(screenshot_path)
        return screenshot_path
    except Exception as e:
        return None
    

def crawl_website(url):
    options = Options()
    options.headless = True

    driver = webdriver.Chrome(options=options)


    try:
        driver.get(url)
        time.sleep(6)

        metadata = extract_metadata(driver,url)

        crawl_data = {
            "url": url,
            "crawl": {
                "loadedUrl": url,
                "loadedTime": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
                "referrerUrl": driver.current_url,  
                "depth": 0  
            },
            "metadata": metadata,
            "screenshotUrl": capture_screenshot(driver),
            "text": driver.find_element(By.TAG_NAME, 'body').text,  
            "html": driver.page_source,  # Full HTML source
            "markdown": "Sample markdown content."  
        }

        return crawl_data
    finally:
        driver.quit()


if __name__ == "__main__":
    url = "https://example.com"
    crawl_data = crawl_website(url)

    output = "result.json"
    with open(output, "w", encoding="utf-8") as file:
        json.dump(crawl_data, file, indent =2)

    print(f"result saved to {output}.")
    

    # print(json.dumps(crawl_data, indent=4))

    