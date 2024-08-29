import time

from block_twitter_spam.utils import click, create_driver


def login(driver):
    while not click(driver, "次へ", "button"):
        time.sleep(1)

    while not click(driver, "ログイン", "span", size=(20, 68)):
        time.sleep(1)


def login_from_banner(driver):
    while not click(driver, "ログイン", "span"):
        time.sleep(1)

    while not click(driver, "次へ", "button"):
        time.sleep(1)

    while not click(driver, "ログイン", "span", size=(20, 68)):
        time.sleep(1)


if __name__ == '__main__':
    driver = create_driver()
    login_from_banner(driver)  # click(driver, "ログイン", "span")
