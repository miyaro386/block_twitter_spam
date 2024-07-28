import os.path

import pandas
import pandas as pd
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from tqdm import tqdm

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=chrome_options)

# %%
def wait_all_elements_available(elements):
    for i in range(10):
        time.sleep(1)
        try:
            for element in elements:
                element.text
        except Exception:
            continue
        break
    if i == 19:
        raise TimeoutError


# %%
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


# %%

def recursive_search(all_lst, lst, depth=0):
    tmp_lst = []
    for i, v in enumerate(lst):
        print(depth, f"{i}/{len(lst)}")
        for retry in range(10):
            try:
                new_lst = get_list_spam_verified_followers(v)
            except TimeoutError:
                print(f"retry {retry}/10")
                time.sleep(10)
                pass
            break
        tmp_lst += new_lst
    new_lst = tmp_lst
    new_lst = list(set(new_lst))

    if depth == 2:
        all_lst += new_lst
        all_lst = list(set(all_lst))
        return all_lst
    return recursive_search(all_lst, new_lst, depth + 1)


if __name__ == '__main__':
    filepath = "spam_id.csv"
    if os.path.exists(filepath):
        df = pandas.read_csv(filepath)
        all_targets = df["user_id"].values.tolist()
        statuses = df["status"].values.tolist()
    else:
        all_targets = []
        start_id = "DungarSiyag0"
        recursive_search(all_targets, [start_id])
        all_targets = list(set(all_targets))
        all_targets = list(set(all_targets))
        statuses = ["alive"] * len(all_targets)
        df = pd.DataFrame.from_dict({"user_id": all_targets, "status": status})
        df.to_csv(filepath)

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


