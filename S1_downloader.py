import sys
import time
import requests
import json
import re
import os
from bs4 import BeautifulSoup
from PyQt5.QtCore import (QThread, pyqtSignal)
import threading
from multiprocessing.dummy import Pool as ThreadPool

def second_to_timestr(t):
    if t < 60:
        return '%d秒' % round(t)
    elif t < 3600:
        return '%d分%d秒' % (t // 60, round(t) % 60)
    else:
        return '%d小时%d分%d秒' % (t // 3600, (t % 3600) % 60, round(t) % 60)

class WorkThread(QThread):
    trigger = pyqtSignal(list)
    def __init__(self):
        super(WorkThread, self).__init__()
        self.url = ''
        self.sess = requests.Session()
    
    def download_source(self, source):
        if not source:
            return None
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
                self.trigger.emit(['process', source])
                resp = self.sess.get(source)
                if resp.status_code == 200:
                    with open('data/' + source_filename, 'wb+') as file:
                        file.write(resp.content)
                    return source_filename
                else:
                    print(source)
                    return None
            except Exception as e:
                self.trigger.emit(['error', e])
                return None
        else:
            return source_filename
                
    def change_path(self, todo_list, keyword):
        todo_list = list(filter(lambda x: x.get(keyword), todo_list))
        for j in range(3):
            source_list = [x.get(keyword) for x in todo_list]
            # print(source_list)
            pool = ThreadPool(processes=4)
            source_filename_list = pool.map(self.download_source, source_list)
            pool.close()
            pool.join()
            next_todo_list = []
            for i in range(len(source_filename_list)):
                source_filename = source_filename_list[i]
                if source_filename:
                    todo_list[i][keyword] = source_filename
                else:
                    next_todo_list.append(todo_list[i])
            if len(next_todo_list) == 0:    #全部下载完成，直接返回
                return True
            else:                           #部分下载失败，继续下载
                todo_list = next_todo_list
                print(len(todo_list))
                time.sleep(1)
        for i in range(len(todo_list)):
            source = todo_list[i].get(keyword)
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
                #删除.css后的多余部分
                for x in css_list:
                    if x.get('href'):
                        x['href'] = re.sub(r'\.css\?[^"\']+', r'.css', x['href'])
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
                time.sleep(5 * (j + 1))
        return False

    def download_thread(self, url, force_refresh=False, pn_range=None):
        '''
        url为待下载专楼地址，支持'https://bbs.saraba1st.com/2b/thread-{tid}-{page}-1.html'与
                               'https://bbs.saraba1st.com/2b/forum.php?mod=viewthread&tid={tid}&page={page}'两种格式
        force_refresh为是否强制更新，若否，下载时会跳过已经存在的页面。默认为否。
        pn_range为下载页数范围，默认为全部页数，支持(1, 5), (3, -2)两种写法
        '''
        self.trigger.emit(['start'])
        total_page = 0
        title = ''
        for j in range(3):
            try:
                page = self.sess.get(url).text
                soup = BeautifulSoup(page, 'html.parser')
                total_page = int((re.findall(r'<span title="共 (\d+) 页">', page) + [1])[0])
                title = soup.find('h1').find('a').text + ' ' + soup.find('h1').find('span').text
                break
            except Exception as e:
                self.trigger.emit(['error', e])
                time.sleep((j+1) * 2)
        if title == '':
            self.trigger.emit(['error', '下载失败，请检查网络联通性与帖子所需权限<br>'])
            return False
        self.trigger.emit(['refresh', 1, total_page, title])
        try:
            try:
                filename = re.findall(r'thread-\d+-\d+-1.html', url)[0]
            except:
                tid = re.findall(r'tid=(\d+)', url)[0]
                page = re.findall(r'page=(\d+)', url)[0]
                filename = 'thread-%s-%s-1.html' % (tid, page)
        except:
            self.trigger.emit(['error', '不是有效的S1帖子地址，请重新检查！'])
        url_template = re.sub(r'(thread-\d+-)(\d+?)(-\d)', r'\1%d\3',filename)
        self.download_page(filename, soup=soup, force_refresh=force_refresh)
        if not pn_range:
            pn_range = (1, total_page + 1)
        else:
            for j in range(2):
                if pn_range[j] < 0:
                    pn_range[j] = total_page + 1 - pn_range[j]
        print(pn_range)
        for i in range(*pn_range):
            print('第%d页' % i, end='\r')
            self.download_page(url_template % i, force_refresh=force_refresh)
            self.trigger.emit(['refresh', i, total_page, title])
        with open('%s.html' % title, 'w+', encoding='utf-8') as file:
            file.write('<head><meta http-equiv="refresh" content="0;url=data/%s"></head>' % (url_template % pn_range[0]))
            self.trigger.emit(['finished', total_page, title])
        return total_page

    def run(self):
        try:
            self.download_thread(self.url)
        except Exception as e:
            self.trigger.emit(['error', e])

if __name__ == '__main__':
    wt = WorkThread()
    wt.url = 'https://bbs.saraba1st.com/2b/thread-1911768-1-1.html'
    while True:
        total_page = wt.download_thread('https://bbs.saraba1st.com/2b/thread-1911768-1-1.html', force_refresh=True)
        print(time.strftime("%m-%d %H:%M:%S", time.localtime()), total_page)
        time.sleep(600)
