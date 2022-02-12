from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
import time

email_link = "https://www.proximus.be/smoothAccess/nl/redirector?lat=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJCSUxMSU5HIiwicGEiOiIxIiwiYnMiOiJGTFMiLCJuYW1lIjoiUFJPSkVDVCBXSFkiLCJpc3MiOiJPQ1QiLCJleHAiOjE2NDk3MTQyMjgsImp0aSI6IkZMUzAwMDAwMDAwOTU0Nzk4MTA2IiwiY2lkIjoiNjI0NDMzODk0In0.GdDe7ZsWqNujFmmvFgis9qI_m0Kt86Wrgt0o7dOQkV8-wHn975pG-ia713603ggWzQ_a8H4maKKw06kTMA48GxN_HIzwdVovrzXB1p0Hn837c78ldESTkEkik4ZdDl6zWHc2_KSY90v6CmCGOLzYi4izgERG8PcmHjIbIQyAFvmQ8Odpj6uCbksz4wjJoUXIdz-g17FN4hjgQI7O2WZXKKLj-i17-jSWPEe4OMFbRsL_J4Gz2p_BVRe2B3kHDKwrxxNHIwhE2xjid55JGvFirDGOWxNT3QiEivR6AmMwfaG7yXtNm6IwCEzYaCCvnRA8dac6Am9a7Faj36Nxtuok2w"
three_dots = "/html/body/div/div/section/main/my-bill-app/div/my-bill-overview-container/div/section/div[3]/div/div/my-bill-billing-account-container/div/div[2]/my-bill-open-transaction-card/div/my-bill-transaction-card-header/div/my-bill-three-dot-menu/div/div/button"
pdf_download = "/html/body/div/div/section/main/my-bill-app/div/my-bill-overview-container/div/section/div[3]/div/div/my-bill-billing-account-container/div/div[2]/my-bill-open-transaction-card/div/my-bill-transaction-card-header/div/my-bill-three-dot-menu/div/div/div/ul/li[1]/my-bill-pdf-document/a"


def set_chrome_options() -> None:
    """Sets chrome options for Selenium.
    Chrome options for headless browser is enabled.
    """
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
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


def navigate_proximus(driver):
    driver.get(email_link)
    iframe = driver.find_element(By.TAG_NAME, "iframe")
    driver.switch_to.frame(iframe)
    wrap(driver.find_element)(By.CLASS_NAME, "call").click()
    wrap(driver.find_element)(By.XPATH, three_dots).click()
    wrap(driver.find_element)(By.XPATH, pdf_download).click()


if __name__ == "__main__":
    driver = webdriver.Chrome(options=set_chrome_options())
    navigate_proximus(driver=driver)
    while True:
        try:
            pass
        except KeyboardInterrupt:
            break
    # Do stuff with your driver
    driver.close()
