

class Item:
    def __repr__(self):
        return f'song: {self.song} singer: {self.singer} album: {self.album} ext: {self.ext} ' \
               f'filename: {self.filename} duration: {self.duration} size: {self.size} url: {self.url} ' \
               f'download: {self.download}'

    def __init__(self, song: str = '', singer: str = '', album: str = '', ext: str = '', filename: str = '',
                 duration: int = 0, size: int = 0, url: str = '', download: bool = False):
        self.song = song
        self.singer = singer
        self.album = album
        self.ext = ext
        self.filename = filename
        self.duration = duration
        self.size = size
        self.url = url
        self.download = download

        if self.filename == '':
            infos = []
            if song != '':
                infos.append(song)
            if singer != '':
                infos.append(singer)
            if album != '':
                infos.append(album)
            self.filename = '-'.join(infos) + ext

    def __getitem__(self, item):
        return self.__getattribute__(item)

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __lt__(self, other):
        return str(self) < str(other)


if __name__ == '__main__':
    items = [Item(singer='123', song='a'), Item(singer='123', song='b'), Item(singer='456', song='a'),
             Item(singer='1234', song='a')]
    items = sorted(items)
    for item in items:
        print(item)
