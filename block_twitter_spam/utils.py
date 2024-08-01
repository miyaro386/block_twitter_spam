import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


def wait_all_elements_available(elements):
    for i in range(10):
        try:
            for element in elements:
                element.text
        except Exception as e:
            time.sleep(1)
            continue
        break
    if i == 19:
        raise TimeoutError


def retry_wrapper(n_retry=10, wait=60):
    def _retry_wrapper(func):
        def wrapper(*args, **kwargs):
            for retry in range(n_retry):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"retry {retry}/10, {e}")
                    time.sleep(wait)
            raise TimeoutError
        return wrapper
    return _retry_wrapper


def create_driver():
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def check_text_exists(driver, text, label):
    elements = driver.find_elements(By.XPATH, f'//{label}')
    wait_all_elements_available(elements)
    for element in elements:
        if text in element.text:
            return True
    return False

def click(driver, text, label, attr_type="text"):
    elements = driver.find_elements(By.XPATH, f'//{label}')
    wait_all_elements_available(elements)
    for element in elements:
        if text in getattr(element, attr_type):
            element.click()
            return True
    return False


def check_empty_page():
    logs = []
    elements = driver.find_elements(By.XPATH, '//button')
    wait_all_elements_available(elements)
    for element in elements:
        log = (element.accessible_name, element.text, element.tag_name, element.aria_role)
        logs.append(log)
    if len(elements) == 1:
        return True
    else:
        return False
