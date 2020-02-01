import sys
import time
from PyQt5.QtWidgets import (QPushButton, QProgressBar, QWidget, QApplication, QLineEdit,
                             QFileDialog, QLabel, QGridLayout, QMessageBox)
from PyQt5.QtCore import (QThread, pyqtSignal, QDate)
from PyQt5.QtGui import (QIcon, QPixmap, QFont)
import requests
import json
import re
import os
from bs4 import BeautifulSoup

def second_to_timestr(t):
    if t < 60:
        return '%d秒' % round(t)
    elif t < 3600:
        return '%d分%d秒' % (t // 60, round(t) % 60)
    else:
        return '%d小时%d分%d秒' % (t // 3600, (t % 3600) % 60, round(t) % 60)

class WorkThread(QThread):
    trigger = pyqtSignal(list)
    sess = requests
    def __int__(self):
        super(WorkThread, self).__init__()
        self.url = ''        
    
    def download_source(self, source):
        source_root = 'source/'
        if not re.match('http', source):
            if re.match('//', source):
                source = 'http:' + source
            else:
                source = 'https://bbs.saraba1st.com/2b' + ('/' if source[0] != '/' else '') + source
        #新浪图床将https前缀改为http即可下载
        if re.match(r'.+\.sinaimg\..+', source):
            source = source.replace('https', 'http')

        source_filename = source_root + re.sub(r'[\\:*?"<>|]', '_', source.split('//')[1])
        os.makedirs(os.getcwd().replace('\\', '/') + '/data/' + '/'.join(source_filename.split('/')[:-1]), exist_ok=True)
        if not os.path.exists('data/' + source_filename):
            try:
                with open('data/' + source_filename, 'wb+') as file:
                    self.trigger.emit(['process', source])
                    file.write(self.sess.get(source).content)
                    if 'saraba1st' in source:
                        time.sleep(0.2)
            except Exception as e:
                self.trigger.emit(['error', e])
                return None
        else:
            return source_filename
                
    def change_path(self, todo_list, keyword):
        for i in range(len(todo_list)):
            source = todo_list[i].get(keyword)
            if source:
                flag = True
                for j in range(5):
                    source_filename = self.download_source(source)
                    if source_filename:
                        todo_list[i][keyword] = source_filename
                        flag = False
                        break
                    else:
                        time.sleep((j+1) * 5)
                if flag:
                    # self.trigger.emit(["error", source])
                    if '//' not in source:
                        todo_list[i][keyword] = 'https://bbs.saraba1st.com/2b' + ('/' if source[0] != '/' else '') + source

    def download_page(self, filename, soup=None, force_refresh=False):
        #若文件已存在且非强制更新模式，不进行下载
        if os.path.exists('data/' + filename) and not force_refresh:
            return True
        for j in range(5):
            try:
                if not soup:
                    time.sleep(2)
                    page = self.sess.get('https://bbs.saraba1st.com/2b/' + filename, timeout=30).text
                    soup = BeautifulSoup(page, 'html.parser')
                img_list = soup.find_all('img') 
                script_list = list(filter(lambda x: x.get('src') and 'google' not in x.get('src') and 'home.php' not in x.get('src')
                                        , soup.find_all('script')))    
                css_list = list(filter(lambda x: x.get('rel') == ['stylesheet'], soup.find_all('link')))
                for img in img_list:
                    if img.get('src') == 'source/static.saraba1st.com/image/common/none.gif':
                        img['src'] = img.get('file', 'source/static.saraba1st.com/image/common/none.gif')
                self.change_path(css_list, 'href')
                self.change_path(script_list, 'src')
                self.change_path(img_list, 'src')
                self.change_path(img_list, 'file')
                self.change_path(img_list, 'zoomfile')
                with open('data/' + filename, 'w+', encoding='utf-8') as file:
                    file.write(soup.prettify())
                return True
            except Exception as e:
                self.trigger.emit(['error', e])
                time.sleep(10 * (j + 1))
        return False

    def download_thread(self, url, force_refresh=False, pn_range=None):
        self.trigger.emit(['start'])
        page = self.sess.get(url).text
        soup = BeautifulSoup(page, 'html.parser')
        title = soup.find('h1').find('a').text + ' ' + soup.find('h1').find('span').text
        total_page = int(re.findall(r'<span title="共 (\d+) 页">', page)[0])
        self.trigger.emit(['refresh', 1, total_page, title])
        try:
            filename = re.findall(r'thread-\d+-\d+-1.html', url)[0]
        except:
            tid = re.findall(r'tid=(\d+)', url)[0]
            page = re.findall(r'page=(\d+)', url)[0]
            filename = 'thread-%s-%s-1.html' % (tid, page)
        url_template = re.sub(r'(thread-\d+-)(\d+?)(-\d)', r'\1%d\3',filename)
        self.download_page(filename, soup=soup)
        if not pn_range:
            pn_range = (1, total_page + 1)
        else:
            for j in range(2):
                if pn_range[j] < 0:
                    pn_range[j] = total_page + 1 - pn_range[j]
        for i in range(*pn_range):
            self.download_page(url_template % i, force_refresh)
            self.trigger.emit(['refresh', i, total_page, title])
        with open('%s.html' % title, 'w+', encoding='utf-8') as file:
            file.write('<head><meta http-equiv="refresh" content="0;url=data/%s"></head>' % (url_template % pn_range[0]))
            self.trigger.emit(['finished', total_page, title])

    def run(self):
        self.download_thread(self.url)

class Login_Dialog(QWidget):
    log_trigger= pyqtSignal(list)
    def __init__(self):
        super().__init__()
        self.username = QLineEdit(self)
        self.password = QLineEdit(self)
        self.password.setEchoMode(QLineEdit.Password)
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()
        # for [col, width] in [[1, 2], [2, 10], [3, 1], [4, 10], [5, 10]]:
        #     layout.setColumnMinimumWidth(col, width)
        # layout.setColumnStretch(3, 0.01)

        self.setWindowTitle('用户登录')
        self.setGeometry(760, 390, 200, 100)
        self.setLayout(layout)

        information = QLabel('<font size="2">部分需要权限的帖子登录后才能下载<br>此外未登录情况无法获得用户信息<br>'\
            '本工具不会用任何途径获取、保存您的用户名与密码<br>程序代码<a href="https://github.com/shuangluoxss/Stage1st-downloader">已开源</a>，请放心使用</font>')
        layout.addWidget(information, 1, 1, 2, 3)

        layout.addWidget(QLabel('用户名：'), 3, 1, 1, 1)
        layout.addWidget(self.username, 3, 2, 1, 2)
        layout.addWidget(QLabel('密码：'), 4, 1, 1, 1)
        layout.addWidget(self.password, 4, 2, 1, 2)

        login_button = QPushButton("登录", self)
        login_button.clicked.connect(self.login)
        layout.addWidget(login_button, 5, 2, 1, 1)

        exit_button = QPushButton("退出", self)
        exit_button.clicked.connect(self.exit)
        layout.addWidget(exit_button, 5, 3, 1, 1)

        
        
        
    def login(self):
        username = self.username.text()
        password = self.password.text()
        sess = requests.Session()
        resp = sess.post("https://bbs.saraba1st.com/2b/member.php?mod=logging&action=login&loginsubmit=yes&infloat=yes&lssubmit=yes&inajax=1",
                data={'username': username, 'password': password}).text
        if 'https://bbs.saraba1st.com/2b/./' in resp:
            sess.headers.update({
                                    'Host': 'bbs.saraba1st.com',
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
                                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                                    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
                                    'Accept-Encoding': 'gzip, deflate, br',
                                    'Connection': 'keep-alive'
                                })
            self.log_trigger.emit([sess])
            QMessageBox.information(self,"", "登陆成功！", QMessageBox.Yes|QMessageBox.No, QMessageBox.Yes)
            self.close()
        else:
            QMessageBox.warning(self,"","登陆失败！",QMessageBox.Yes|QMessageBox.No,QMessageBox.Yes)


    def exit(self):
        self.close()

class Main(QWidget):
    def __init__(self):
        super().__init__()
        self.workThread = WorkThread(self)
        self.message = QLabel(self)
        self.message2 = QLabel(self)
        self.pbar = QProgressBar(self)
        self.t1 = 0
        self.url = QLineEdit(self)
        self.loginDlg = Login_Dialog()
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()
        layout.addWidget(self.pbar, 1, 1, 1, 5)
        self.workThread.trigger.connect(self.refresh_progressbar)
        self.loginDlg.log_trigger.connect(self.get_sess)

        self.message.setText('无下载任务')
        layout.addWidget(self.message, 2, 1, 1, 5)
        self.message2.setText('')
        layout.addWidget(self.message2, 3, 1, 1, 5)

        self.setWindowTitle('S1专楼下载器')
        self.setGeometry(560, 460, 800, 160)
        self.setLayout(layout)

        layout.addWidget(QLabel('帖子地址：'), 4, 1, 1, 1)
        self.url.setText('')
        layout.addWidget(self.url, 4, 2, 1, 4)

        login_button = QPushButton("登录", self)
        login_button.clicked.connect(self.login)
        layout.addWidget(login_button, 5, 2, 1, 1)

        logout_button = QPushButton("登出", self)
        logout_button.clicked.connect(self.logout)
        layout.addWidget(logout_button, 5, 3, 1, 1)

        start_button = QPushButton("开始下载", self)
        start_button.clicked.connect(self.get_all)
        layout.addWidget(start_button, 5, 4, 1, 1)

        exit_button = QPushButton("退出", self)
        exit_button.clicked.connect(self.exit)
        layout.addWidget(exit_button, 5, 5, 1, 1)
        
    def refresh_progressbar(self, paras):
        if paras[0] == 'start':
            self.message.setText('下载中……')
            self.t1 = time.time()
            self.message2.setText('<font size="3">正在下载：第%d页</font>' % (1))
        elif paras[0] == 'refresh':
            self.pbar.setMaximum(paras[2])
            self.pbar.setValue(paras[1])
            self.message.setText('<div><div style="float:left;"><b>%s</b></div><div align="right" style="float:right;">%d/%d页</div></div>' % (paras[3], paras[1], paras[2]))
            self.message2.setText('<font size="3">正在下载：第%d页</font>' % (paras[1] + 1))
        elif paras[0] == 'finished':
            self.message.setText('<b>%s</b><br>下载完成, 总用时：%s' % (paras[2], second_to_timestr(time.time() - self.t1)))            
            self.message2.setText('')
        elif paras[0] == 'process':
            self.message2.setText('<font size="3">正在下载：%s</font>' % paras[1])
        elif paras[0] == 'error':
            self.message2.setText('<font size="3" color="red">%s</font>' % str(paras[1]))

    def get_all(self):
        self.workThread.url = self.url.text()
        self.workThread.start()

    def login(self):
        self.loginDlg.show()

    def logout(self):
        self.workThread.sess = requests
        QMessageBox.information(self,"", "登出成功！", QMessageBox.Yes|QMessageBox.No, QMessageBox.Yes)

    def get_sess(self, paras):
        self.workThread.sess = paras[0]

    def exit(self):
        self.close()


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    font = QFont()
    font.setPointSize(10)
    app.setFont(font)
    icon = QIcon()
    icon.addPixmap(QPixmap(resource_path('favicon.ico')), QIcon.Normal, QIcon.Off)
    ex = Main()
    ex.setWindowIcon(icon)
    ex.loginDlg.setWindowIcon(icon)
    ex.show()
    app.exec_()
