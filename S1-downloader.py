import requests
import json
import re
from bs4 import BeautifulSoup
import os
import time

source_root = 'source/'
sess = requests.Session()
sess.headers.update({
                        'Host': 'bbs.saraba1st.com',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive'
                    })
        
def login(username, password):
    global sess
    resp = sess.post("https://bbs.saraba1st.com/2b/member.php?mod=logging&action=login&loginsubmit=yes&infloat=yes&lssubmit=yes&inajax=1",
                data={'username': username, 'password': password}).text
    if 'https://bbs.saraba1st.com/2b/./' in resp:
        print('登陆成功')
    else:
        print(resp)

def download_source(source):
    global sess
    global source_root
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
                print(source, end='\r')
                file.write(sess.get(source).content)
                if 'saraba1st' in source:
                    time.sleep(0.2)
        except Exception as e:
            print(e)
            return None
    else:
        return source_filename
            
def change_path(todo_list, keyword):
    global sess
    for i in range(len(todo_list)):
        source = todo_list[i].get(keyword)
        if source:
            flag = True
            for j in range(5):
                source_filename = download_source(source)
                if source_filename:
                    todo_list[i][keyword] = source_filename
                    flag = False
                    break
                else:
                    time.sleep((j+1) * 5)
            if flag:
                print("%s下载失败" % source)
                if '//' not in source:
                    todo_list[i][keyword] = 'https://bbs.saraba1st.com/2b' + ('/' if source[0] != '/' else '') + source
                
def download_page(filename, soup=None, force_refresh=False):
    global sess
    #若文件已存在且非强制更新模式，不进行下载
    if os.path.exists('data/' + filename) and not force_refresh:
        return True
    for j in range(5):
        try:
            if not soup:
                time.sleep(2)
                page =  sess.get('https://bbs.saraba1st.com/2b/' + filename, timeout=30).text
                soup = BeautifulSoup(page, 'html.parser')
            img_list = soup.find_all('img') 
            script_list = list(filter(lambda x: x.get('src') and 'google' not in x.get('src') and 'home.php' not in x.get('src')
                                      , soup.find_all('script')))    
            css_list = list(filter(lambda x: x.get('rel') == ['stylesheet'], soup.find_all('link')))
            for img in img_list:
                if img.get('src') == 'source/static.saraba1st.com/image/common/none.gif':
                    img['src'] = img.get('file', 'source/static.saraba1st.com/image/common/none.gif')
            change_path(css_list, 'href')
            change_path(script_list, 'src')
            change_path(img_list, 'src')
            change_path(img_list, 'file')
            change_path(img_list, 'zoomfile')
            with open('data/' + filename, 'w+', encoding='utf-8') as file:
                file.write(soup.prettify())
            return True
        except Exception as e:
            print(filename, j, e)
            time.sleep(10 * (j + 1))
    return False


def download_thread(url, force_refresh=False, pn_range=None):
    '''
    url为待下载专楼地址，支持'https://bbs.saraba1st.com/2b/thread-{tid}-{page}-1.html'与
                           'https://bbs.saraba1st.com/2b/forum.php?mod=viewthread&tid={tid}&page={page}'两种格式
    force_refresh为是否强制更新，若否，下载时会跳过已经存在的页面。默认为否。
    pn_range为下载页数范围，默认为全部页数，支持(1, 5), (3, -2)两种写法
    '''
    global sess
    t0 = time.time()
    page = sess.get(url).text
    soup = BeautifulSoup(page, 'html.parser')
    title = soup.find('h1').find('a').text + ' ' + soup.find('h1').find('span').text
    total_page = int(re.findall('<span title="共 (\d+) 页">', page)[0])
    print("%s, 共 %d 页" % (title, total_page))
    try:
        filename = re.findall(r'thread-\d+-\d+-1.html', url)[0]
    except:
        tid = re.findall(r'tid=(\d+)', url)[0]
        page = re.findall(r'page=(\d+)', url)[0]
        filename = 'thread-%s-%s-1.html' % (tid, page)
    url_template = re.sub(r'(thread-\d+-)(\d+?)(-\d)', r'\1%d\3',filename)
    download_page(filename, soup=soup)
    if not pn_range:
        pn_range = (1, total_page + 1)
    else:
        for j in range(2):
            if pn_range[j] < 0:
                pn_range[j] = total + 1 - pn_range[j]
    for i in range(*pn_range):
        download_page(url_template % i, force_refresh)
        print('%d/%d, Time used: %.1fs' % (i, total_page, time.time() - t0), end='\r')
    print('%d/%d, Time used: %.1fs' % (total_page, total_page, time.time() - t0), end='\r')
    with open('%s.html' % title, 'w+', encoding='utf-8') as file:
        file.write('<head><meta http-equiv="refresh" content="0;url=data/%s"></head>' % (url_template % pn_range[0]))


#login(username, password)
for thread in [ 'https://bbs.saraba1st.com/2b/thread-1910469-1-1.html',
                'https://bbs.saraba1st.com/2b/thread-1910781-1-1.html',
                'https://bbs.saraba1st.com/2b/thread-1911312-1-1.html']:
    download_thread(thread)