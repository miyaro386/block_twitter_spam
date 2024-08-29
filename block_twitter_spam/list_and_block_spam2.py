import argparse
import os.path
import time

import pandas
import pandas as pd
from selenium.common import StaleElementReferenceException
from selenium.webdriver.common.by import By
from tqdm import tqdm

from block_twitter_spam.block_spam import block
from block_twitter_spam.list_spam import get_list_spam_verified_followers, get_list_spam_verified_followers2
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
        status = ["alive"] * len(targets)
        df = pd.DataFrame({"user_id": targets, "status": status})
        df.to_csv(args.filepath, index=False)
    else:
        df = pandas.read_csv(filepath)

    driver = create_driver()

    try:
        while True:
            if all([v == "listed" for v in df["status"].values]):
                break

            for i, row in tqdm(df.iterrows(), total=len(df)):
                if not row.status == "listed":
                    break

            user_id = row.user_id

            driver.get(f'https://x.com/{user_id}/verified_followers')
            time.sleep(3)

            new_targets = get_list_spam_verified_followers2(driver)
            df.at[i, "status"] = "listed"
            if len(new_targets) == 0:
                df.to_csv(filepath, index=False)
                continue

            new_status = ["alive"] * len(new_targets)
            new_df = pd.DataFrame({"user_id": new_targets, "status": new_status})

            df = pd.concat([df, new_df])
            df.to_csv(filepath, index=False)

            elements = driver.find_elements(By.XPATH, '//div')
            time.sleep(1)
            for element in elements[100:]:
                try:
                    if "おすすめユーザー" == element.text:
                        break
                    if element.text.encode("unicode-escape") == b'\\U0001f171\\ufe0f':
                        element.click()
                        time.sleep(1)
                except StaleElementReferenceException as e:
                    print(e)
                    break

    except KeyboardInterrupt:
        print("KeyboardInterrupt")


if __name__ == '__main__':
    main()
