# -*- encoding: utf-8 -*-

"""
@File    :   util.py
@Time    :   2024/3/12 13:15:33
@Author  :   lh9171338
@Version :   1.0
@Contact :   2909171338@qq.com
"""

import time
import logging


def printTime(func):
    def wrapper(*args, **kwargs):
        t = time.time()
        res = func(*args, **kwargs)
        logging.info(f"{func.__name__} time: {time.time() - t:.3f}")
        return res

    return wrapper
