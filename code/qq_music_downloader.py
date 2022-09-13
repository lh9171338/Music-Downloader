import os
import sys
from yacs.config import CfgNode
import logging
import requests
import json
from typing import Type
from PyQt5.QtWidgets import *
from util import printTime
from item import Item
from search import SearchWorker
from music_downloader import MusicDownloader


class QQSearchWorker(SearchWorker):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Variables
        self.search_url = 'https://u.y.qq.com/cgi-bin/musicu.fcg'
        self.download_url = 'https://dl.stream.qqmusic.qq.com/'
        self.search_data = {'req': {
            'method': 'DoSearchForQQMusicDesktop',
            'module': 'music.search.SearchCgiService',
            'param': {'query': '', 'page_num': 1, 'num_per_page': self.cfg.search.pagesize}}
        }
        self.parse_data = {'req': {
            'method': 'CgiGetVkey',
            'module': 'vkey.GetVkeyServer',
            'param': {'guid': '0', 'songmid': [], 'songtype': []}}
        }

    @printTime
    def run(self) -> None:
        self.items = []

        # Search
        data = self.search_data
        data['req']['param']['query'] = self.keyword
        data = json.dumps(data, ensure_ascii=False)
        data = data.encode('utf-8')
        try:
            res = requests.post(self.search_url, data)
            js = res.json()
            results1 = js['req']['data']['body']['song']['list']
        except Exception as e:
            logging.error(str(e))
        else:
            mids = [result['mid'] for result in results1]
            types = [result['type'] for result in results1]
            data = self.parse_data
            data['req']['param']['songmid'] = mids
            data['req']['param']['songtype'] = types
            data = json.dumps(data, ensure_ascii=False)
            data = data.encode('utf-8')
            try:
                res = requests.post(self.search_url, data)
                js = res.json()
                results2 = js['req']['data']['midurlinfo']
                for result1, result2 in zip(results1, results2):
                    purl = result2['purl']
                    if purl == '':
                        continue
                    singer = result1['singer'][0]['name']
                    song = result1['title']
                    album = result1['album']['name']
                    duration = result1['interval']
                    url = self.download_url + purl
                    item = Item(song=song,
                                singer=singer,
                                album=album,
                                ext='.m4a',
                                duration=duration,
                                size=0,
                                url=url,
                                )
                    self.items.append(item)
            except Exception as e:
                logging.error(str(e))
        logging.info(f'Found {len(self.items)} songs')
        self.finished.emit()


class QQMusicDownloader(MusicDownloader):
    def __init__(self, searcher: Type[SearchWorker] = QQSearchWorker, **kwargs):
        super().__init__(searcher=searcher, **kwargs)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(threadName)s:%(message)s')
    root_path = sys.path[0]
    cfg_file = os.path.join(root_path, '..', 'config', 'default.yaml')
    cfg = CfgNode.load_cfg(open(cfg_file))
    cfg.freeze()

    app = QApplication(sys.argv)
    window = QQMusicDownloader(cfg=cfg)
    sys.exit(app.exec_())
