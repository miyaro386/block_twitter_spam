import time


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
