import os
import sys
from yacs.config import CfgNode
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from typing import List, Type
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from search import SearchWorker
from download import DownloadWorker, AsyncDownloadWorker


class MusicDownloader(QMainWindow):
    search_started = pyqtSignal()
    download_started = pyqtSignal()

    def __init__(self, cfg: CfgNode, searcher: Type[SearchWorker],
                 downloader: Type[DownloadWorker] = AsyncDownloadWorker, **kwargs):
        super().__init__(**kwargs)

        root_path = sys.path[0]
        save_path = os.path.join(root_path, '..', cfg.file.save_folder)

        # Variables
        service = Service(os.path.join(root_path, '../tool/chromedriver.exe'))
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--headless')
        self.driver = webdriver.Chrome(service=service, options=options)

        self.play_index = None
        self.items = []
        self.num_items = 0

        self.search_thread = QThread()
        self.search_worker = searcher(cfg=cfg)
        self.search_worker.moveToThread(self.search_thread)
        self.search_worker.finished.connect(self.searchFinishCallback)
        self.search_started.connect(self.search_worker.run)
        self.search_thread.start()

        self.download_thread = QThread()
        self.download_worker = downloader(save_path=save_path)
        self.download_worker.moveToThread(self.download_thread)
        self.download_worker.finished.connect(self.downloadFinishCallback)
        self.download_started.connect(self.download_worker.run)
        self.download_thread.start()

        # Parameters
        self.infosize = cfg.window.infosize
        self.pagesize = cfg.window.pagesize
        self.page = 0
        self.num_page_items = 0
        self.num_pages = 0
        self.check_status = [False] * self.pagesize
        self.check_indices = []

        self.window_size = cfg.window.window_size
        self.margin = cfg.window.margin

        # UI
        # Icon
        self.icon_play = QIcon(os.path.join(root_path, '..', cfg.file.play_icon_file))
        self.icon_stop = QIcon(os.path.join(root_path, '..', cfg.file.stop_icon_file))
        self.icon_download = QIcon(os.path.join(root_path, '..', cfg.file.download_icon_file))
        self.icon_prev = QIcon(os.path.join(root_path, '..', cfg.file.prev_icon_file))
        self.icon_next = QIcon(os.path.join(root_path, '..', cfg.file.next_icon_file))

        # Head
        self.edit_keyword = QLineEdit()
        self.button_download = QPushButton(self.icon_download, '下载')
        self.layout_head = QHBoxLayout()
        self.layout_head.addWidget(self.edit_keyword)
        self.layout_head.addStretch(1)
        self.layout_head.addWidget(self.button_download)

        # Body
        self.layout_body = QVBoxLayout()
        self.check_item = QCheckBox()
        self.label_song = QLabel()
        self.label_duration = QLabel()
        self.label_size = QLabel()
        self.label_play = QLabel()
        self.layout_item = QHBoxLayout()
        self.layout_item.addWidget(self.check_item)
        self.layout_item.addWidget(self.label_song, stretch=1)
        self.layout_item.addWidget(self.label_duration)
        self.layout_item.addWidget(self.label_size)
        self.layout_item.addWidget(self.label_play)
        self.layout_body.addLayout(self.layout_item)

        self.check_items = [QCheckBox() for _ in range(self.pagesize)]
        self.label_songs = [QLabel() for _ in range(self.pagesize)]
        self.label_durations = [QLabel() for _ in range(self.pagesize)]
        self.label_sizes = [QLabel() for _ in range(self.pagesize)]
        self.button_plays = [QPushButton(self.icon_stop, '') for _ in range(self.pagesize)]
        self.layout_items = [QHBoxLayout() for _ in range(self.pagesize)]
        for i in range(self.pagesize):
            self.layout_items[i].addWidget(self.check_items[i])
            self.layout_items[i].addWidget(self.label_songs[i], stretch=1)
            self.layout_items[i].addWidget(self.label_durations[i])
            self.layout_items[i].addWidget(self.label_sizes[i])
            self.layout_items[i].addWidget(self.button_plays[i])
            self.button_plays[i].setCheckable(True)
            self.layout_body.addLayout(self.layout_items[i])

        # Tail
        self.label_page = QLabel()
        self.label_page.setAlignment(Qt.AlignCenter)
        self.button_prev = QPushButton(self.icon_prev, '')
        self.button_next = QPushButton(self.icon_next, '')
        self.layout_tail = QHBoxLayout()
        self.layout_tail.addWidget(self.button_prev)
        self.layout_tail.addWidget(self.label_page)
        self.layout_tail.addWidget(self.button_next)

        self.layout = QVBoxLayout()
        self.layout.addLayout(self.layout_head)
        self.layout.addLayout(self.layout_body)
        self.layout.addStretch(1)
        self.layout.addLayout(self.layout_tail)

        self.centralWidget = QWidget()
        self.centralWidget.setLayout(self.layout)
        self.centralWidget.setContentsMargins(self.margin, 0, self.margin, 0)
        self.setCentralWidget(self.centralWidget)
        self.setWindowTitle(self.__class__.__name__)
        if self.window_size is not None:
            self.setFixedSize(self.window_size[0], self.window_size[1])

        # Register callback
        self.edit_keyword.editingFinished.connect(self.editKeywordCallback)
        self.button_download.clicked.connect(self.buttonDownloadCallback)
        self.check_item.clicked.connect(self.checkItemCallback)
        self.button_prev.clicked.connect(self.buttonPrevCallback)
        self.button_next.clicked.connect(self.buttonNextCallback)
        for i in range(self.pagesize):
            self.check_items[i].clicked.connect(self.checkItemCallback)
            self.button_plays[i].clicked.connect(self.buttonPlayCallback)

        self.setVisibleAll(False)
        self.show()

    def setVisibleAll(self, visible: bool):
        self.button_download.setEnabled(False)
        self.check_item.setVisible(visible)
        self.label_song.setText('歌曲名' if visible else '')
        self.label_duration.setText('时长 ' if visible else '')
        self.label_size.setText('大小  ' if visible else '')
        self.label_play.setText('播放' if visible else '')

        for i in range(self.pagesize):
            self.check_items[i].setVisible(visible)
            self.label_songs[i].setText('')
            self.label_durations[i].setText('')
            self.label_sizes[i].setText('')
            self.button_plays[i].setVisible(visible)

        self.label_page.setText('')
        self.button_prev.setVisible(visible)
        self.button_next.setVisible(visible)

    def updateCheckBox(self):
        num_checks = sum(self.check_status)
        self.button_download.setEnabled(num_checks)
        self.check_item.setChecked(num_checks == self.num_page_items)
        for i in range(self.pagesize):
            index = self.page * self.pagesize + i
            if i < self.num_page_items:
                self.check_items[i].setVisible(True)
                self.check_items[i].setChecked(self.check_status[i])
                self.check_items[i].setEnabled(not self.items[index].download)
            else:
                self.check_items[i].setVisible(False)

    def updateInfo(self):
        for i in range(self.pagesize):
            index = self.page * self.pagesize + i
            if i < self.num_page_items:
                item = self.items[index]
                song_info = os.path.splitext(item.filename)[0][:self.infosize]
                duration_info = f'{item.duration // 60:02d}:{item.duration % 60:02d}' if item.duration > 0 else '  --  '
                size_info = f'{item.size / 1048576:.2f}MB' if item.size > 0 else '  --  '
                self.label_songs[i].setText(song_info)
                self.label_durations[i].setText(duration_info)
                self.label_sizes[i].setText(size_info)
            else:
                self.label_songs[i].setText('')
                self.label_durations[i].setText('')
                self.label_sizes[i].setText('')

    def updatePlayButton(self):
        for i in range(self.pagesize):
            if i < self.num_page_items:
                self.button_plays[i].setVisible(True)
                self.button_plays[i].setChecked(False)
                self.button_plays[i].setIcon(self.icon_stop)
            else:
                self.button_plays[i].setVisible(False)
        if self.play_index is not None:
            self.button_plays[self.play_index].setChecked(True)
            self.button_plays[self.play_index].setIcon(self.icon_play)

    def updatePage(self):
        if self.play_index is not None:
            self.driver.back()
            self.play_index = None

        self.button_prev.setEnabled(self.page > 0)
        self.button_next.setEnabled(self.page < self.num_pages - 1)
        self.label_page.setText(f'{self.page + 1}/{self.num_pages}')

    def updateAll(self):
        self.updatePage()
        self.updateCheckBox()
        self.updateInfo()
        self.updatePlayButton()

    def editKeywordCallback(self):
        if not self.edit_keyword.hasFocus():
            return
        keyword = self.edit_keyword.text()
        self.search_worker.setKeyword(keyword)
        self.search_started.emit()

        # Disable all widgets
        self.setEnabled(False)

    def searchFinishCallback(self):
        self.setEnabled(True)
        items = self.search_worker.getItems()
        if items:
            if not self.items:
                self.setVisibleAll(True)
            self.items = sorted(items)
            self.num_items = len(self.items)
            self.num_pages = self.num_items // self.pagesize + (self.num_items % self.pagesize > 0)
            self.page = 0
            self.num_page_items = min(self.pagesize, self.num_items - self.page * self.pagesize)
            self.check_status = [False] * self.num_page_items
            self.updateAll()
        else:
            msg_box = QMessageBox(QMessageBox.Warning, 'warning', 'No content found!', QMessageBox.Ok)
            msg_box.button(QMessageBox.Ok).animateClick(1000)
            msg_box.exec_()
            if self.items:
                self.updatePage()
                self.updateCheckBox()

    def buttonDownloadCallback(self):
        items = []
        self.check_indices = []
        for i in range(self.num_page_items):
            if self.check_status[i]:
                self.check_indices.append(i)
                index = self.page * self.pagesize + i
                items.append(self.items[index])

        self.download_worker.setItems(items)
        self.download_started.emit()

        # Disable all widgets
        self.setEnabled(False)

    def downloadFinishCallback(self):
        results = self.download_worker.getResults()
        failure = 0
        for i, result in zip(self.check_indices, results):
            if result:
                index = self.page * self.pagesize + i
                self.check_status[i] = False
                self.items[index].download = True
            else:
                failure += 1
        if failure == 0:
            msg_box = QMessageBox(QMessageBox.Information, 'information', 'All files downloaded successfully!',
                                  QMessageBox.Ok)
            msg_box.button(QMessageBox.Ok).animateClick(1000)
            msg_box.exec_()
        else:
            QMessageBox.warning(self, 'warning', f'{failure} files failed to download!')
        self.setEnabled(True)
        self.updateCheckBox()

    def buttonPrevCallback(self):
        self.page -= 1
        self.num_page_items = min(self.pagesize, self.num_items - self.page * self.pagesize)
        self.check_status = [False] * self.num_page_items
        self.updateAll()

    def buttonNextCallback(self):
        self.page += 1
        self.num_page_items = min(self.pagesize, self.num_items - self.page * self.pagesize)
        self.check_status = [False] * self.num_page_items
        self.updateAll()

    def checkItemCallback(self):
        if self.sender() == self.check_item:
            is_checked = self.check_item.isChecked()
            self.check_status = [is_checked] * self.num_page_items
        else:
            for i in range(self.num_page_items):
                self.check_status[i] = self.check_items[i].isChecked()
        self.updateCheckBox()

    def buttonPlayCallback(self):
        index = 0
        for i in range(self.num_page_items):
            if self.sender() == self.button_plays[i]:
                index = i
                break
        if self.button_plays[index].isChecked():
            url_index = self.page * self.pagesize + index
            self.play_index = index
            url = self.items[url_index].url
            self.driver.get(url)
        else:
            self.play_index = None
            self.driver.back()
        self.updatePlayButton()

    def closeEvent(self, a0: QCloseEvent):
        self.search_thread.exit()
        self.download_thread.exit()
        self.driver.close()
