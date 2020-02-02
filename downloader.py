import requests
import logging
import re
import os
import time
from multiprocessing.dummy import Pool as ThreadPool
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def login(username, password, on_success, on_fail):
    # on_success: 登录成功成功回调方法 sess: session
    # on_fail: 登录失败时回调
    sess = requests.Session()
    resp = sess.post(
        "https://bbs.saraba1st.com/2b/member.php?mod=logging&action=login&loginsubmit=yes&infloat=yes&lssubmit=yes&inajax=1",
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
        on_success(sess)
    else:
        on_fail()


# 下载器类（与 PyQt 分离）
class S1Downloader(object):
    def __init__(self):
        self.sess = requests.Session()
        # 异常
        self.on_exception = self.empty
        # 出错
        self.on_error = self.empty
        # 更新状态
        self.on_update = self.empty
        # 开始下载
        self.on_start = self.empty
        # 下载完成时
        self.on_finish = self.empty
        # 处理 xx 文件时
        self.on_process = self.empty

    # 占坑用 不知道有没有更好的实现
    def empty(self, *args):
        pass

    # 下载源文件
    def download_source(self, source):
        source_root = 'source/'
        if not source:
            return None
        if not re.match('http', source):
            # 生成 URL
            if re.match('//', source):
                source = 'http:' + source
            else:
                source = 'https://bbs.saraba1st.com/2b' + ('/' if source[0] != '/' else '') + source
            # 新浪图床将https前缀改为http即可下载
            if re.match(r'.+\.sinaimg\..+', source):
                source = source.replace('https', 'http')
            # 辨析文件名
            source_filename = source_root + re.sub(r'[\\:*?"<>|]', '_', source.split('//')[1])
            logger.debug("downloader source = %s, filename = %s", source, source_filename)

            os.makedirs(os.getcwd().replace('\\', '/') + '/data/' + '/'.join(source_filename.split('/')[:-1]),
                        exist_ok=True)
            # 文件不存在时
            if not os.path.exists('data/' + source_filename):
                logger.debug("downloader getting file: filename = %s" % source_filename)
                try:
                    self.on_process(source)
                    resp = self.sess.get(source)
                    if resp.status_code == 200:
                        with open('data/' + source_filename, 'wb+') as file:
                            file.write(resp.content)
                        return source_filename
                    else:
                        logger.warning("File failed to download. Source = %s, HTTP status code = %d",
                                       source, resp.status_code)
                        return None
                except Exception as e:
                    self.on_exception(e)
                    return None
            else:
                return source_filename

    # 修改网页中指向的资源地址
    def change_path(self, todo_list, keyword):
        todo_list = list(filter(lambda x: x.get(keyword), todo_list))
        for j in range(3):
            source_list = [x.get(keyword) for x in todo_list]
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
            if len(next_todo_list) == 0:  # 全部下载完成，直接返回
                return True
            else:  # 部分下载失败，继续下载
                todo_list = next_todo_list
                logger.debug("%d files failed to download." % len(todo_list))
                time.sleep(2)
        for i in range(len(todo_list)):
            source = todo_list[i].get(keyword)
            if '//' not in source:
                todo_list[i][keyword] = 'https://bbs.saraba1st.com/2b' + ('/' if source[0] != '/' else '') + source

    # 下载页面
    def download_page(self, filename, soup=None, force_refresh=False):
        # 若文件已存在且非强制更新模式，不进行下载
        if os.path.exists('data/' + filename) and not force_refresh:
            return True
        for j in range(5):
            try:
                if not soup:
                    time.sleep(2)
                    page = self.sess.get('https://bbs.saraba1st.com/2b/' + filename, timeout=30).text
                    soup = BeautifulSoup(page, 'html.parser')
                img_list = soup.find_all('img')
                script_list = list(
                    filter(lambda x: x.get('src') and 'google' not in x.get('src') and 'home.php' not in x.get('src')
                           , soup.find_all('script')))
                css_list = list(filter(lambda x: x.get('rel') == ['stylesheet'], soup.find_all('link')))
                for img in img_list:
                    if img.get('src') == 'source/static.saraba1st.com/image/common/none.gif':
                        img['src'] = img.get('file', 'source/static.saraba1st.com/image/common/none.gif')
                # 删除.css后的多余部分
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
                self.on_exception(e)
        return False

    # 下载帖子
    def download_thread(self, url, force_refresh=False, pn_range=None):
        """
        url为待下载专楼地址，支持'https://bbs.saraba1st.com/2b/thread-{tid}-{page}-1.html'与
                               'https://bbs.saraba1st.com/2b/forum.php?mod=viewthread&tid={tid}&page={page}'两种格式
        force_refresh为是否强制更新，若否，下载时会跳过已经存在的页面。默认为否。
        pn_range为下载页数范围，默认为全部页数，支持(1, 5), (3, -2)两种写法
        """
        self.on_start()
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
                logger.error(e)
                self.on_exception(e)
                time.sleep((j + 1) * 2)
        if title == '':
            logger.error("Download failed. Please check Internet connection or authorization.")
            self.on_error('下载失败，请检查网络联通性与帖子所需权限<br>')
            return False
        # 更新进度
        self.on_update(1, total_page, title)
        try:
            try:
                file_name = re.findall(r'thread-\d+-\d+-1.html', url)[0]
            except:
                tid = re.findall(r'tid=(\d+)', url)[0]
                page = re.findall(r'page=(\d+)', url)[0]
                file_name = 'thread-%s-%s-1.html' % (tid, page)
        except:
            logger.error('Invalid thread address. url = %s' % url)
            self.on_error('不是有效的S1帖子地址，请重新检查！')
        url_template = re.sub(r'(thread-\d+-)(\d+?)(-\d)', r'\1%d\3', file_name)
        self.download_page(file_name, soup=soup, force_refresh=force_refresh)
        if not pn_range:
            pn_range = (1, total_page + 1)
        else:
            for j in range(2):
                if pn_range[j] < 0:
                    pn_range[j] = total_page + 1 - pn_range[j]
        # print(pn_range)
        logger.debug(pn_range)
        for i in range(*pn_range):
            # print('第%d页' % i, end='\r')
            logger.debug('Page %d' % i)
            self.download_page(url_template % i, force_refresh=force_refresh)
            # 更新进度
            self.on_update(i, total_page, title)
        with open('%s.html' % re.sub(r'[\\/:*?"<>|]', '_', title), 'w+', encoding='utf-8') as file:
            file.write(
                '<head><meta http-equiv="refresh" content="0;url=data/%s"></head>' % (url_template % pn_range[0]))
            # 更新进度
            self.on_finish(total_page, title)
        return total_page
