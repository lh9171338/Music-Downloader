import os
import sys
import urllib.parse
import requests
from yacs.config import CfgNode
import logging
from typing import Type
from PyQt5.QtWidgets import *
from util import printTime
from item import Item
from search import SearchWorker
from music_downloader import MusicDownloader


class NeteaseCloudSearchWorker(SearchWorker):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Variables
        self.search_url = 'https://music.163.com/api/search/get'
        self.download_url = 'https://music.163.com/api/song/enhance/player/url?ids=%s&csrf_token=&br=999000'
        self.search_data = {
            's': '',
            'type': 1,
            'offset': 0,
            'sub': 'false',
            'limit': self.cfg.search.pagesize
        }

    @printTime
    def run(self) -> None:
        self.items = []

        # Search
        data = self.search_data
        data['s'] = self.keyword
        data = urllib.parse.urlencode(data).encode('utf-8')
        try:
            res = requests.get(self.search_url, data)
            js = res.json()
            results1 = js['result']['songs']
            results1 = sorted(results1, key=lambda x: x['id'])
            song_ids = [result['id'] for result in results1]
            download_url = self.download_url % str(song_ids)
            res = requests.get(download_url)
            js = res.json()
            results2 = js['data']
            results2 = sorted(results2, key=lambda x: x['id'])
            for result1, result2 in zip(results1, results2):
                singer = result1['artists'][0]['name']
                song = result1['name']
                album = result1['album']['name']
                duration = int(round(result2['time'] / 1000))
                size = result2['size']
                url = result2['url']
                if url is None or url == '':
                    continue
                item = Item(song=song,
                            singer=singer,
                            album=album,
                            ext='.mp3',
                            duration=duration,
                            size=size,
                            url=url,
                            )
                self.items.append(item)
        except Exception as e:
            logging.error(str(e))
        logging.info(f'Found {len(self.items)} songs')
        self.finished.emit()


class NeteaseCloudMusicDownloader(MusicDownloader):
    def __init__(self, searcher: Type[SearchWorker] = NeteaseCloudSearchWorker, **kwargs):
        super().__init__(searcher=searcher, **kwargs)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(threadName)s:%(message)s')
    root_path = sys.path[0]
    cfg_file = os.path.join(root_path, '..', 'config', 'default.yaml')
    cfg = CfgNode.load_cfg(open(cfg_file))
    cfg.freeze()

    app = QApplication(sys.argv)
    window = NeteaseCloudMusicDownloader(cfg=cfg)
    sys.exit(app.exec_())
