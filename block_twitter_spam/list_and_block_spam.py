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

from block_twitter_spam.list_spam import recursive_search, get_list_spam_verified_followers
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
    parser.add_argument("-s", "--start_id", type=str, nargs="*")
    parser.add_argument("-f", "--filepath", type=str, default="spam_list.csv")
    args = parser.parse_args()

    filepath = args.filepath
    if not os.path.exists(filepath):
        targets = args.start_id
        statuses = ["alive"] * len(targets)
        listed = [False] * len(targets)
        df = pd.DataFrame({"user_id": targets, "status": statuses, "listed": listed})
        df.to_csv(args.filepath)

    df = pandas.read_csv(filepath)

    try:
        while True:
            for i, row in tqdm(df.iterrows(), total=len(df)):
                listed = row.listed
                if not listed:
                    user_id = row.user_id
                    new_targets = get_list_spam_verified_followers(user_id)
                    df.at[i, "listed"] = True
                    new_statuses = ["alive"] * len(new_targets)
                    new_listed = [False] * len(new_targets)
                    new_df = pd.DataFrame({"user_id": new_targets, "status": new_statuses, "listed": new_listed})
                    df = pd.concat([df, new_df])
                    df.to_csv(filepath)
                    break

            for i, row in tqdm(df.iterrows(), total=len(df)):
                status = row.status
                if status == "blocked":
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

                    except StaleElementReferenceException:
                        driver = create_driver()
                        continue
                    except Exception as e:
                        print(e)
                        print(f"retry {retry}/10")
                        continue

                df.at[i, "status"] = result
                df.to_csv(filepath)

    except KeyboardInterrupt:
        print("KeyboardInterrupt")


if __name__ == '__main__':
    main()
