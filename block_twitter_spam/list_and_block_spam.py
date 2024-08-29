import argparse
import os.path
import time

import pandas
import pandas as pd
from selenium.common import StaleElementReferenceException
from selenium.webdriver.common.by import By
from tqdm import tqdm

from block_twitter_spam.block_spam import block
from block_twitter_spam.list_spam import get_list_spam_verified_followers
from block_twitter_spam.login import login_from_banner, login
from block_twitter_spam.utils import wait_all_elements_available, create_driver, check_text_exists


def main():
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

    driver = create_driver()

    try:
        while True:
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
                        if any([element.text == "Xにログイン" for element in elements]):
                            print("login")
                            login(driver)
                            continue
                        if any([element.text == "ログイン" for element in elements]):
                            print("login_from_banner")
                            login_from_banner(driver)
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
                        if check_text_exists(driver, "ブロック中", "button"):
                            print(f"{user_id} ブロック中")
                            result = "blocked"
                            break

                        result = block(driver)
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

            for i, row in tqdm(df.iterrows(), total=len(df)):
                listed = row.listed
                if not listed:
                    user_id = row.user_id
                    new_targets = get_list_spam_verified_followers(driver, user_id)
                    df.at[i, "listed"] = True
                    new_statuses = ["alive"] * len(new_targets)
                    new_listed = [False] * len(new_targets)
                    new_df = pd.DataFrame({"user_id": new_targets, "status": new_statuses, "listed": new_listed})
                    df = pd.concat([df, new_df])
                    df.to_csv(filepath)
                    break

    except KeyboardInterrupt:
        print("KeyboardInterrupt")


if __name__ == '__main__':
    main()
