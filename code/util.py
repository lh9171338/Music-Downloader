import time
import logging


def printTime(func):
    def wrapper(*args, **kwargs):
        t = time.time()
        res = func(*args, **kwargs)
        logging.info(f'{func.__name__} time: {time.time() - t:.3f}')
        return res

    return wrapper
