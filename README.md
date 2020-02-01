# Stage1st论坛专楼下载器

## 简介

使用python实现，原理是用requests下载帖子每页的html，然后将其中所有css、script和图片保存至本地

- 优势
   * 下载后的帖子可以离线翻页，方便阅读
   * 不同帖子共用css、图片等资源，节约空间
   * 自动将新浪外链图片的https替换为http
   * 包含登录功能，可下载需要权限的帖子
   
- 不足
   * 删除下载的帖子时无法删除其中图片
   * 下载速度非常慢（鉴于论坛服务器的现状，暂不考虑多线程等提速手段）
   * ~~GUI非常丑~~
   
程序非常简单，全部源码在[S1-downloader.py](https://github.com/shuangluoxss/Stage1st-downloader/blob/master/S1-downloader.py)中，熟悉python的坛友可以在此基础上自行修改

为方便使用，用PyQt5做了一个简陋的GUI并打包了成exe，相关源码在[S1-downloader_GUI.py](https://github.com/shuangluoxss/Stage1st-downloader/blob/master/S1-downloader_gui.py)中

## 使用方法
**（网页保存位置默认为程序运行位置）**
- python版本
   * 下载地址：[S1-downloader_GUI.py](https://github.com/shuangluoxss/Stage1st-downloader/blob/master/S1-downloader_gui.py)
   * `download_thread(url)`下载url所在专楼的所有页，其余参数用法见注释
   * ~~会python的直接看源码去，懒得写说明了~~
- exe版本
   * 下载地址：[S1-downloader_v0.1.zip](https://github.com/shuangluoxss/Stage1st-downloader/releases/download/v0.1/S1-downloader_v0.1.zip)
   * 双击运行，在帖子地址中粘贴帖子地址，点开始下载即可
   * 若需要登录，点击“登录”，输入账号密码
   
## 使用建议
- 由于下载速度主要由论坛响应速度决定，建议在论坛流量较小时使用
- 由于论坛帖子有大量共用素材（麻将脸等），当这部分素材下载完毕后，帖子下载速度会得到显著提升
- 由于作者水平所限，程序大概会有很多bug，如果大家使用中遇到问题欢迎在论坛或这里反馈，有希望添加的功能也欢迎提出~
