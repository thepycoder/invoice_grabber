from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
import time

import config

def set_chrome_options() -> None:
    """Sets chrome options for Selenium.
    Chrome options for headless browser is enabled.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--proxy-server='direct://'")
    chrome_options.add_argument("--proxy-bypass-list=*")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument('--lang=nl_BE')
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_prefs = {}
    chrome_options.experimental_options["prefs"] = chrome_prefs
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    chrome_prefs["download.default_directory"] = "/content"
    return chrome_options


def wrap(method, exceptions = (NoSuchElementException)):
    def fn(*args, **kwargs):
        for _ in range(5):
            try:
                return method(*args, **kwargs)
            except exceptions:
                time.sleep(0.5)
                continue
        raise Exception('We tried too much!')

    return fn


def navigate_proximus(email_link):
    driver = webdriver.Chrome(options=set_chrome_options())
    driver.get(email_link)
    driver.save_screenshot("screenshot.png")
    # iframe = driver.find_element(By.TAG_NAME, "iframe")
    # driver.switch_to.frame(iframe)
    # wrap(driver.find_element)(By.CLASS_NAME, "call").click()
    invoice_string = wrap(driver.find_element)(By.XPATH, config.INVOICE_NR)
    invoice_nr = invoice_string.string.split(' ')[-1]
    wrap(driver.find_element)(By.XPATH, config.THREE_DOTS).click()
    wrap(driver.find_element)(By.XPATH, config.PDF_DOWNLOAD).click()

    # Wait for the download to be complete
    time.sleep(10)
    driver.close()

    return invoice_nr


if __name__ == "__main__":
    invoice_nr = navigate_proximus(email_link=config.EMAIL_LINK)
