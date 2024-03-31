# -*- encoding: utf-8 -*-

"""
@File    :   kugou_music_downloader.py
@Time    :   2024/3/12 13:15:33
@Author  :   lh9171338
@Version :   1.0
@Contact :   2909171338@qq.com
"""

import os
import sys
from yacs.config import CfgNode
import logging
import requests
import aiohttp
import asyncio
import json
from typing import Dict, Type
from PyQt5.QtWidgets import *
from util import printTime
from item import Item
from search import SearchWorker
from music_downloader import MusicDownloader


class KuGouSearchWorker(SearchWorker):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Variables
        search_url = "https://songsearch.kugou.com/song_search_v2?keyword={}&pagesize=%d"
        self.search_url = search_url % self.cfg.search.pagesize
        self.hash_url = (
            "https://www.kugou.com/yy/index.php?r=play/getdata&hash={}"
        )
        self.cookies = {"kg_mid": "2333"}

    @printTime
    def run(self) -> None:
        self.items = []
        search_url = self.search_url.format(self.keyword)
        try:
            res = requests.get(search_url)
            results = res.json()["data"]["lists"]
        except Exception as e:
            logging.error(str(e))
        else:
            for result in results:
                song = result["SongName"]
                singer = result["Singers"][0]["name"]
                album = result["AlbumName"]
                file_hash = result["FileHash"]
                duration = result["Duration"]
                size = result["FileSize"]
                hash_url = self.hash_url.format(file_hash)
                try:
                    res = requests.get(hash_url, cookies=self.cookies)
                    data = res.json()["data"]
                    if "play_url" in data and data["play_url"] != "":
                        url = data["play_url"]
                        item = Item(
                            song=song,
                            singer=singer,
                            album=album,
                            ext=".mp3",
                            duration=duration,
                            size=size,
                            url=url,
                        )
                        self.items.append(item)
                except Exception as e:
                    logging.error(str(e))
                    continue
        logging.info(f"Found {len(self.items)} songs")
        self.finished.emit()


class AsyncKuGouSearchWorker(KuGouSearchWorker):
    async def func(
        self, result: Dict[str, any], session: aiohttp.ClientSession
    ) -> Item:
        item = None
        file_hash = result["FileHash"]
        hash_url = self.hash_url.format(file_hash)
        try:
            res = await session.get(hash_url, cookies=self.cookies)
            text = await res.text()
            data = json.loads(text)["data"]
            if "play_url" in data and data["play_url"] != "":
                song = result["SongName"]
                singer = result["Singers"][0]["name"]
                album = result["AlbumName"]
                duration = result["Duration"]
                size = result["FileSize"]
                url = data["play_url"]
                item = Item(
                    song=song,
                    singer=singer,
                    album=album,
                    ext=".mp3",
                    duration=duration,
                    size=size,
                    url=url,
                )
        except Exception as e:
            logging.error(str(e))

        return item

    async def main(self) -> None:
        self.items = []
        search_url = self.search_url.format(self.keyword)
        try:
            res = requests.get(search_url)
            results = res.json()["data"]["lists"]
        except Exception as e:
            logging.error(str(e))
        else:
            async with aiohttp.ClientSession() as session:
                tasks = [
                    asyncio.create_task(self.func(result, session))
                    for result in results
                ]
                finished, unfinished = await asyncio.wait(tasks)
                self.items = [f.result() for f in finished if f.result()]
                logging.info(f"Found {len(self.items)} songs")

    @printTime
    def run(self) -> None:
        # Disable RuntimeError: Event loop is closed

        asyncio.run(self.main())
        self.finished.emit()


class KuGouMusicDownloader(MusicDownloader):
    def __init__(
        self, searcher: Type[SearchWorker] = AsyncKuGouSearchWorker, **kwargs
    ):
        super().__init__(searcher=searcher, **kwargs)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s:%(name)s:%(threadName)s:%(message)s",
    )
    root_path = sys.path[0]
    cfg_file = os.path.join(root_path, "..", "config", "default.yaml")
    cfg = CfgNode.load_cfg(open(cfg_file))
    cfg.freeze()

    app = QApplication(sys.argv)
    window = KuGouMusicDownloader(cfg=cfg)
    sys.exit(app.exec_())
