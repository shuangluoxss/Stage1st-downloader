import time
from PyQt5.QtCore import (QThread, pyqtSignal)
from downloader import S1Downloader, login


class WorkThread(QThread):
    trigger = pyqtSignal(list)

    def __init__(self):
        super(WorkThread, self).__init__()
        self.url = ''
        # self.sess = requests.Session()
        self.downloader: S1Downloader = S1Downloader()
        self.downloader.on_exception = self.on_exception
        self.downloader.on_error = self.on_error
        self.downloader.on_update = self.on_update
        self.downloader.on_start = self.on_start
        self.downloader.on_finish = self.on_finish
        self.downloader.on_process = self.on_process

    def on_exception(self, e):
        self.trigger.emit(['error', e])

    def on_error(self, msg):
        self.trigger.emit(['error', msg])

    def on_update(self, current_page, total_pages, title):
        self.trigger.emit(['refresh', current_page, total_pages, title])

    def on_start(self):
        self.trigger.emit(['start'])

    def on_finish(self, total_pages, title):
        self.trigger.emit(['finished', total_pages, title])

    def on_process(self, source):
        self.trigger.emit(['process', source])

    def run(self):
        try:
            self.downloader.download_thread(self.url)
        except Exception as e:
            self.trigger.emit(['error', e])


if __name__ == '__main__':
    wt = WorkThread()
    wt.url = 'https://bbs.saraba1st.com/2b/thread-1911768-1-1.html'
    while True:
        total_page = wt.download_thread('https://bbs.saraba1st.com/2b/thread-1911768-1-1.html', force_refresh=True)
        print(time.strftime("%m-%d %H:%M:%S", time.localtime()), total_page)
        time.sleep(600)
