from yacs.config import CfgNode
from typing import List
from PyQt5.QtCore import *
from util import printTime
from item import Item


class SearchWorker(QObject):
    finished = pyqtSignal()

    def __init__(self, cfg: CfgNode, **kwargs):
        super().__init__(**kwargs)

        self.cfg = cfg
        self.keyword = None
        self.items = None

    def setKeyword(self, keyword: str) -> None:
        self.keyword = keyword

    def getItems(self) -> List[Item]:
        return self.items

    @printTime
    def run(self) -> None:
        raise NotImplementedError
