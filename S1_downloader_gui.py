from S1_downloader import *
from PyQt5.QtWidgets import (QPushButton, QProgressBar, QWidget, QApplication, QLineEdit,
                             QFileDialog, QLabel, QGridLayout, QMessageBox)
from PyQt5.QtCore import (QThread, pyqtSignal)
from PyQt5.QtGui import (QIcon, QPixmap, QFont)
from bs4 import BeautifulSoup

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
        self.workThread = WorkThread()
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
        self.message.setWordWrap(True)
        self.message2.setText('')
        layout.addWidget(self.message2, 3, 1, 1, 5)
        self.message2.setWordWrap(True)

        self.setWindowTitle('S1专楼下载器')
        self.setGeometry(560, 460, 800, 160)
        self.setLayout(layout)
        # self.setFixedSize(800, 160)

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
