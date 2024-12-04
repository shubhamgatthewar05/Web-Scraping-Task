import time
import json
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import html2text
from bs4 import BeautifulSoup


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def configure_driver(headless=True):
    """Configure and return a Selenium WebDriver."""
    options = Options()
    options.headless = headless
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--start-maximized")
    return webdriver.Chrome(options=options)


def dynamic_scroll(driver, timeout=10):
    """Perform dynamic scrolling to load all content."""
    logger.info("Starting dynamic scrolling...")
    scroll_pause_time = 1
    last_height = driver.execute_script("return document.body.scrollHeight")

    start_time = time.time()
    while time.time() - start_time < timeout:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def extract_metadata(driver):
    """Extract metadata like title, description, and author."""
    logger.info("Extracting metadata...")
    metadata = {}
    try:
        metadata['title'] = driver.title
    except Exception as e:
        logger.warning(f"Error extracting title: {e}")
        metadata['title'] = None

    meta_tags = {
        'description': "//meta[@name='description']",
        'author': "//meta[@name='author']",
        'keywords': "//meta[@name='keywords']"
    }

    for key, xpath in meta_tags.items():
        try:
            metadata[key] = driver.find_element(By.XPATH, xpath).get_attribute('content')
        except Exception:
            metadata[key] = None

    try:
        metadata['language'] = driver.find_element(By.XPATH, "//html").get_attribute('lang')
    except Exception:
        metadata['language'] = None

    metadata['canonicalUrl'] = driver.current_url
    return metadata


def remove_unnecessary_elements(driver):
    """Remove unwanted elements like ads, navigation bars, and modals."""
    logger.info("Removing unnecessary elements...")
    elements_to_remove = [
        "//header", "//footer", "//nav",
        "//div[contains(@class, 'ads')]",
        "//div[contains(@class, 'modal')]",
        "//div[contains(@id, 'cookie')]"
    ]
    for xpath in elements_to_remove:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for element in elements:
                driver.execute_script("arguments[0].remove();", element)
        except Exception as e:
            logger.warning(f"Error removing elements with xpath '{xpath}': {e}")


def capture_screenshot(driver, output_path="screenshot.png"):
    """Capture and save a screenshot of the current webpage."""
    try:
        driver.save_screenshot(output_path)
        logger.info(f"Screenshot saved to {output_path}")
        return output_path
    except Exception as e:
        logger.warning(f"Error capturing screenshot: {e}")
        return None


def extract_main_content(html_content):
    """Extract the main content from the HTML using BeautifulSoup."""
    soup = BeautifulSoup(html_content, "html.parser")

    # Try to find the main content area
    main_content = soup.find("main") or soup.find("article")
    if not main_content:
        # Fallback to body content if <main> or <article> is not present
        main_content = soup.find("body")

    # Remove unwanted elements
    for tag in main_content.find_all(["header", "footer", "nav", "script", "style", "aside", "form"]):
        tag.decompose()

    # Optionally remove comments
    for comment in main_content.find_all(string=lambda text: isinstance(text, BeautifulSoup.Comment)):
        comment.extract()

    return str(main_content)


def convert_html_to_markdown_precise(html_content):
    """Convert cleaned HTML content to precise Markdown format."""
    logger.info("Converting HTML to Markdown (Enhanced)...")
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = False
    converter.ignore_emphasis = False
    converter.body_width = 0

    # Extract main content for better accuracy
    main_content = extract_main_content(html_content)
    markdown = converter.handle(main_content)

    # Additional formatting for better readability
    formatted_markdown = (
        markdown.replace("\n\n", "\n")  # Remove excessive newlines
        .replace("###", "##")  # Reduce excessive heading levels
        .strip()
    )

    logger.info("Markdown conversion complete.")
    return formatted_markdown


def parse_clean_html(html_content):
    """Parse and clean HTML using BeautifulSoup."""
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove unnecessary elements .......!
    for tag in soup(["header", "footer", "nav", "aside", "script", "style"]):
        tag.decompose()

    return str(soup)


def save_content(content, filename):
    """Save content to a file."""
    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(content)
        logger.info(f"Content saved to {filename}")
    except Exception as e:
        logger.error(f"Failed to save content to {filename}: {e}")


def crawl_website(url, timeout=10):
    """Main function to crawl a website and extract structured data."""
    driver = configure_driver()
    try:
        driver.get(url)
        logger.info(f"Loaded URL: {url}")
        dynamic_scroll(driver, timeout=timeout)

        # Here Remove unwanted elements for cleaner output
        remove_unnecessary_elements(driver)

        # Here I Extract metadata
        metadata = extract_metadata(driver)

        # Extract full HTML and convert to precise Markdown.....................................................................................................
        html_content = driver.page_source
        clean_html = parse_clean_html(html_content)
        markdown_content = convert_html_to_markdown_precise(clean_html)

        # Extract plain text content
        text_content = driver.find_element(By.TAG_NAME, 'body').text

        # Capture a screenshot of the webpage
        screenshot_path = capture_screenshot(driver)

        # Save content in fromat
        save_content(clean_html, "content.html")  # Save cleaned HTML
        save_content(markdown_content, "content.md")  # Save precise Markdown
        save_content(text_content.strip(), "content.txt")  # Save plain text

        # crawl data
        crawl_data = {
            "url": url,
            "crawl": {
                "loadedUrl": driver.current_url,
                "loadedTime": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
                "referrerUrl": driver.current_url,
                "depth": 0
            },
            "metadata": metadata,
            "screenshotUrl": screenshot_path,
            "text": text_content.strip(),
            "html": clean_html,
            "markdown": markdown_content.strip()
        }

        return crawl_data
    finally:
        driver.quit()


if __name__ == "__main__":
    target_url = "https://console.apify.com/actors/aYG0l9s7dbB7j3gbS/input" 
    try:
        crawl_data = crawl_website(target_url)

       
        output_file = "result.json"
        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(crawl_data, file, indent=2)
        logger.info(f"Result saved to {output_file}")

    except Exception as e:
        logger.error(f"Failed to crawl website: {e}")
