import argparse
import os.path

import pandas
import pandas as pd
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from tqdm import tqdm

from block_twitter_spam.list_spam import recursive_search
from block_twitter_spam.utils import wait_all_elements_available

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=chrome_options)


def block_by_user_id(user_id):
    driver.get(f'https://x.com/{user_id}')
    time.sleep(5)

    elements = driver.find_elements(By.XPATH, '//button')
    wait_all_elements_available(elements)
    for element in elements:
        if "ブロック中" in element.text:
            print(f"{user_id} ブロック中")
            return "blocked"

    for element in elements:
        if element.accessible_name == "もっと見る":
            element.click()
            break

    time.sleep(0.5)
    elements = driver.find_elements(By.XPATH, '//span')
    wait_all_elements_available(elements)
    for element in elements:
        if "をブロック" in element.text:
            element.click()
            break

    time.sleep(0.5)
    elements = driver.find_elements(By.XPATH, '//button')
    wait_all_elements_available(elements)
    for element in elements:
        if "ブロック" in element.text:
            element.click()
            return "blocked"

    return "missing"


if __name__ == '__main__':
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
            target = row.user_id
            for retry in range(10):
                try:
                    result = block_by_user_id(target)
                except Exception:
                    print(f"retry {retry}/10")
                    continue

                if result == "missing":
                    print(f"retry missing {retry}/10")
                    time.sleep(300)
                    driver.refresh()
                    continue
                break
            statuses[i] = result
            tmp_df = pd.DataFrame.from_dict({"user_id": all_targets, "status": statuses})
            tmp_df.to_csv("spam_id.csv")

    except KeyboardInterrupt:
        print("KeyboardInterrupt")

    tmp_df = pd.DataFrame.from_dict({"user_id": all_targets, "status": statuses})
    tmp_df.to_csv("spam_id.csv")

    # # %%
    # elements = driver.find_elements(By.XPATH, '//button')
    # logs = []
    # for element in elements:
    #     log = (element.accessible_name, element.text, element.tag_name, element.aria_role)
    #     print(log)
    #     logs.append(log)
    # # %%
    # elements = driver.find_elements(By.XPATH, '//span')
    # logs = []
    # for element in elements:
    #     log = (element.accessible_name, element.text, element.tag_name, element.aria_role)
    #     print(log)
    #     logs.append(log)


