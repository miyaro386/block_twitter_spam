import argparse
import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from tqdm import tqdm

from block_twitter_spam.utils import wait_all_elements_available, retry_wrapper

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=chrome_options)


@retry_wrapper()
def get_list_spam_verified_followers(user_id):
    driver.get(f'https://x.com/{user_id}/verified_followers')
    time.sleep(5)
    elements = driver.find_elements(By.XPATH, '//button')
    wait_all_elements_available(elements)
    targets = []
    for i, element in enumerate(elements):
        if element.accessible_name == "もっと見る":
            break
        if element.text == "フォロー":
            user_id = element.accessible_name.split("@")[-1]
            targets.append(user_id)
    return targets


def recursive_search(all_targets, targets, _depth=0, recursive_depth=2):
    all_targets += targets

    statuses = ["alive"] * len(all_targets)
    df = pd.DataFrame.from_dict({"user_id": all_targets, "status": statuses})
    df.to_csv(args.output_path)

    if _depth == recursive_depth:
        return
    for i, target in tqdm(enumerate(targets), desc=f"depth={_depth}"):
        new_targets = get_list_spam_verified_followers(target)
        new_targets = list(set(new_targets) - set(all_targets))
        recursive_search(all_targets, new_targets, _depth + 1, recursive_depth=recursive_depth)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--start_id", type=str)
    parser.add_argument("-o", "--output_path", type=str, default="spam_list.csv")
    parser.add_argument("-r", "--recursive_depth", type=int, default=2)
    args = parser.parse_args()

    all_targets = []
    start_id = args.start_id
    recursive_search(all_targets, [start_id], recursive_depth=args.recursive_depth)
