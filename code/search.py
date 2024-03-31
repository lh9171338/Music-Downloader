# -*- encoding: utf-8 -*-

"""
@File    :   search.py
@Time    :   2024/3/12 13:15:33
@Author  :   lh9171338
@Version :   1.0
@Contact :   2909171338@qq.com
"""

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
