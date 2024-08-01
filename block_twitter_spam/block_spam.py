import argparse
import os.path
import time

import pandas
import pandas as pd
from selenium.common import StaleElementReferenceException
from selenium.webdriver.common.by import By
from tqdm import tqdm

from block_twitter_spam.login import login
from block_twitter_spam.utils import wait_all_elements_available, create_driver, check_text_exists, click, \
    check_empty_page


def block(driver):
    while not check_text_exists(driver, "をブロック", "span"):
        click(driver, "もっと見る", "button", attr_type="accessible_name")
        time.sleep(1)

    while not check_text_exists(driver, "ブロック", "button"):
        click(driver, "をブロック", "span")
        time.sleep(1)

    while not check_text_exists(driver, "ブロック中", "button"):
        click(driver, "ブロック", "button")
        time.sleep(1)

    if check_text_exists(driver, "ブロック中", "button"):
        return "blocked"

    return "missing"


def main():
    driver = create_driver()

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
                        login(driver)
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

                    result = block(driver)
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
