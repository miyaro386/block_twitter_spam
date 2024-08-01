import time

from block_twitter_spam.utils import check_text_exists, click, create_driver


def login(driver):
    while not check_text_exists(driver, "次へ", "button"):
        time.sleep(5)
        click(driver, "ログイン", "span")
        time.sleep(1)

    while not check_text_exists(driver, "パスワードを入力", "span"):
        time.sleep(5)
        click(driver, "次へ", "button")
        time.sleep(1)

    click(driver, "ログイン", "button")


if __name__ == '__main__':
    driver = create_driver()
    login(driver)
