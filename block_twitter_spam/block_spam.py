import argparse
import os.path
import time

import pandas
import pandas as pd
from selenium import webdriver
from selenium.common import StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from tqdm import tqdm

from block_twitter_spam.utils import wait_all_elements_available

driver = None


def create_driver():
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=chrome_options)
    return driver


driver = create_driver()


def check_text_exists(text, label):
    elements = driver.find_elements(By.XPATH, f'//{label}')
    wait_all_elements_available(elements)
    for element in elements:
        if text in element.text:
            return True
    return False


def push(text, label, attr_type="text"):
    elements = driver.find_elements(By.XPATH, f'//{label}')
    wait_all_elements_available(elements)
    for element in elements:
        if text in getattr(element, attr_type):
            element.click()
            return True
    return False


def block():
    while not check_text_exists("をブロック", "span"):
        push("もっと見る", "button", attr_type="accessible_name")
        time.sleep(1)

    while not check_text_exists("ブロック", "button"):
        push("をブロック", "span")
        time.sleep(1)

    while not check_text_exists("ブロック中", "button"):
        push("ブロック", "button")
        time.sleep(1)

    if check_text_exists("ブロック中", "button"):
        return "blocked"

    return "missing"


def login():
    global driver

    while not check_text_exists("次へ", "button"):
        push("ログイン", "span")
        time.sleep(1)

    while not check_text_exists("ログイン", "button"):
        push("次へ", "button")
        time.sleep(1)

    push("ログイン", "button")


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


def main():
    global driver

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_spam_list_filepath", type=str, default="spam_list.csv")
    args = parser.parse_args()
    filepath = args.input_spam_list_filepath
    if not os.path.exists(filepath):
        raise FileNotFoundError

    df = pandas.read_csv(filepath)
    all_targets = df["user_id"].values.tolist()
    statuses = df["status"].values.tolist()

    try:
        for i, row in tqdm(df.iterrows(), total=len(df)):
            status = row.status
            if status in ["blocked", "skip"]:
                continue
            user_id = row.user_id
            for retry in range(10):
                try:
                    driver.get(f'https://x.com/{user_id}')
                    time.sleep(1)
                    elements = driver.find_elements(By.XPATH, '//span')
                    wait_all_elements_available(elements)
                    if any([element.text == "ログイン" for element in elements]):
                        login()
                        continue
                    if any([element.text == "アカウントは凍結されています" for element in elements]):
                        result = "blocked"
                        break
                    if any([element.text == "このアカウントは存在しません" for element in elements]):
                        result = "blocked"
                        break
                    if any([element.text == "やりなおす" for element in elements]):
                        print("waiting transaction restriction")
                        time.sleep(600)
                        continue
                    if check_text_exists("ブロック中", "button"):
                        print(f"{user_id} ブロック中")
                        result = "blocked"
                        break

                    result = block()
                    if result == "blocked":
                        break

                    if result == "missing":
                        print(f"retry missing {retry}/10")
                        if check_empty_page():
                            print("empty page")
                            time.sleep(600)
                        # driver.refresh()
                        login()
                        continue
                except StaleElementReferenceException:
                    driver = create_driver()
                    continue
                except Exception as e:
                    print(e)
                    print(f"retry {retry}/10")
                    continue
                result = "error"
                break
            statuses[i] = result
            tmp_df = pd.DataFrame.from_dict({"user_id": all_targets, "status": statuses})
            tmp_df.to_csv(filepath)

    except KeyboardInterrupt:
        print("KeyboardInterrupt")

    tmp_df = pd.DataFrame.from_dict({"user_id": all_targets, "status": statuses})
    tmp_df.to_csv(filepath)


if __name__ == '__main__':
    main()
