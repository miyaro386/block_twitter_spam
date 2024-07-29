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


def retry_wrapper(n_retry=10, wait=60):
    def _retry_wrapper(func):
        def wrapper(*args, **kwargs):
            for retry in range(n_retry):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"retry {retry}/10, {e}")
                    time.sleep(wait)
            raise TimeoutError
        return wrapper
    return _retry_wrapper
