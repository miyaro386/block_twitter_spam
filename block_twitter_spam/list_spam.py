# %%
import time
import argparse
import pandas as pd
from selenium.webdriver.common.by import By

from block_twitter_spam.block_spam import driver
from block_twitter_spam.utils import wait_all_elements_available


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


def recursive_search(all_lst, lst, depth=0, recursive_depth=2):
    tmp_lst = []
    for i, v in enumerate(lst):
        print(depth, f"{i}/{len(lst)}")
        for retry in range(10):
            try:
                new_lst = get_list_spam_verified_followers(v)
            except TimeoutError:
                print(f"retry {retry}/10")
                time.sleep(60)
                pass
            break
        tmp_lst += new_lst
    new_lst = tmp_lst
    new_lst = list(set(new_lst))

    if depth == recursive_depth:
        all_lst += new_lst
        all_lst = list(set(all_lst))
        return all_lst
    return recursive_search(all_lst, new_lst, depth + 1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--start_id", type=str)
    parser.add_argument("-o", "--output_path", type=str, default="spam_list.csv")
    parser.add_argument("-r", "--recursive_depth", type=int, default=2)
    args = parser.parse_args()

    all_targets = []
    start_id = args.start_id
    recursive_search(all_targets, [start_id], recursive_depth=args.recursive_depth)
    all_targets = list(set(all_targets))
    statuses = ["alive"] * len(all_targets)
    df = pd.DataFrame.from_dict({"user_id": all_targets, "status": statuses})
    df.to_csv(args.output_path)
