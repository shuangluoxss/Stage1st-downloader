from downloader import login, S1Downloader
import logging
import argparse
import sys


# 获取输入参数
def get_args():
    parser = argparse.ArgumentParser("S1 Threads downloader.",
                                     description="A tool for using to download Stage1st threads."
                                                 "\nDisclaimer: This program will not "
                                                 "collect any username or password "
                                                 "\nProgram Source code: "
                                                 "https://github.com/PvtTony/Stage1st-downloader")
    parser.add_argument('threads', metavar='threads',
                        type=str, nargs='+', help='Thread urls')
    parser.add_argument('-u', '--user', type=str, help='S1 username')
    parser.add_argument('-p', '--password', type=str, help='S1 user password')
    parser.add_argument('-v', '--verbose', help='Verbose output. (Show debug info)', action="store_true")
    return parser.parse_args()


# 处理输入参数
def process_args(args):
    # 日志完整输出（带调试信息）
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')

    logger = logging.getLogger(__name__)

    def on_exception(e):
        logger.error(e)

    def on_error(msg):
        logger.error(msg)

    def on_update(current_page, total_pages, title):
        print("Downloading %d page, total page: %d pages. Thread title: %s" %
              (current_page, total_pages, title))

    def on_start():
        print("Start downloading")

    def on_finish(total_pages, title):
        print("Thread %s finished successfully. Total pages: %d" % (title, total_pages))

    def on_process(source):
        print("Downloading %s" % source)
        # self.trigger.emit(['process', source])

    downloader: S1Downloader = S1Downloader()
    downloader.on_process = on_process
    downloader.on_finish = on_finish
    downloader.on_start = on_start
    downloader.on_exception = on_exception
    downloader.on_error = on_error
    downloader.on_update = on_update

    def on_login_success(sess):
        print("Login Successful!")
        downloader.sess = sess

    def on_login_fail():
        print('Login Failed. Wrong username or password.')

    if args.user and args.password:
        username = args.user
        password = args.password
        login(username, password, on_success=on_login_success, on_fail=on_login_fail)

    if args.threads and len(args.threads) > 0:
        print('Found %d threads' % len(args.threads))
        for thread_url in args.threads:
            print("Downloading thread url: %s" % thread_url)
            downloader.download_thread(thread_url)


if __name__ == '__main__':
    print("S1 Thread downloader.")
    args = get_args()
    process_args(args)
