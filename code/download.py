# -*- encoding: utf-8 -*-

"""
@File    :   download.py
@Time    :   2024/3/12 13:15:33
@Author  :   lh9171338
@Version :   1.0
@Contact :   2909171338@qq.com
"""

import os
import logging
import requests
import asyncio
import aiohttp
from typing import List
from PyQt5.QtCore import *
from util import printTime
from item import Item


class DownloadWorker(QObject):
    finished = pyqtSignal()

    def __init__(self, save_path: str, **kwargs):
        super().__init__(**kwargs)

        os.makedirs(save_path, exist_ok=True)
        self.save_path = save_path
        self.items = None
        self.results = None

    def setItems(self, items: List[Item]) -> None:
        self.items = items

    def getResults(self) -> List[bool]:
        return self.results

    @printTime
    def run(self) -> None:
        self.results = []
        for item in self.items:
            url = item.url
            filename = item.filename
            result = True
            try:
                res = requests.get(url)
                save_file = os.path.join(self.save_path, filename)
                with open(save_file, "wb") as f:
                    f.write(res.content)
            except Exception as e:
                logging.error(f"Fail to download {filename}", str(e))
                result = False
            self.results.append(result)

        self.finished.emit()


class AsyncDownloadWorker(DownloadWorker):
    async def func(self, item: Item, session: aiohttp.ClientSession) -> bool:
        url = item.url
        filename = item.filename
        result = True
        try:
            res = await session.get(url)
            content = await res.read()
            save_file = os.path.join(self.save_path, filename)
            with open(save_file, "wb") as f:
                f.write(content)
        except Exception as e:
            logging.error(f"Fail to download {filename}", str(e))
            result = False

        return result

    async def main(self, loop: asyncio.AbstractEventLoop) -> None:
        self.results = []
        async with aiohttp.ClientSession() as session:
            tasks = [
                loop.create_task(self.func(item, session))
                for item in self.items
            ]
            finished, unfinished = await asyncio.wait(tasks)
            self.results = [f.result() for f in finished if f.result()]

    @printTime
    def run(self) -> None:
        # Disable RuntimeError: Event loop is closed
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.main(loop))
        self.finished.emit()
