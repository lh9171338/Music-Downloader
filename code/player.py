# -*- encoding: utf-8 -*-

"""
@File    :   player.py
@Time    :   2024/3/12 13:46:01
@Author  :   lh9171338
@Version :   1.0
@Contact :   2909171338@qq.com
"""

from PyQt5.QtWidgets import QApplication
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, QObject


class Player(QObject):
    """
    Music Player
    """

    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer(self)

    def play(self, url):
        url = QUrl(url)
        content = QMediaContent(url)
        self.player.setMedia(content)
        self.player.play()

    def pause(self):
        if self.player.state() == self.player.PlayingState:
            self.player.pause()

    def stop(self):
        if self.player.state() != self.player.StoppedState:
            self.player.stop()


if __name__ == "__main__":
    import sys
    import time

    app = QApplication(sys.argv)
    player = Player()
    player.play(
        "https://dl.stream.qqmusic.qq.com/C400002dCmen3LsUFj.m4a?guid=0&vkey=09EF7F3B37121464616F3350805FEFD02D5149A14BFC2C8693DDB37BFFBBB208C22E040D0A4654C3C1A7CF5FF56333827A570F1E507FE88F&uin=&fromtag=196032"
    )
    sys.exit(app.exec_())
