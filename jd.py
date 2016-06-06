#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2016-06-02 17:04:24
# Project: jd

from pyspider.libs.base_handler import *


class Handler(BaseHandler):
    crawl_config = {
    'itag': 'v1.0',
    'headers': {
    'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'accept-encoding':'gzip, deflate, sdch',
    'accept-language':'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
        'user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
    }
}

    @every(minutes=24 * 60)
    def on_start(self):
        self.crawl('http://www.jd.com/allSort.aspx', callback=self.index_page)

    @config(age=24 * 60 * 60)
    def index_page(self, response):
        for each in response.doc('a[href^="http://list.jd.com/list.html"]').items():
            self.crawl(each.attr.href, callback=self.detail_page, fetch_type='js', auto_recrawl=True)

    @config(priority=2)
    @config(age=6 * 60 * 60)
    def detail_page(self, response):
        for item in response.doc('#plist > ul > li').items():
            url = item('div > div.p-name > a').attr('href')
            self.send_message(self.project_name, {
                'brief_content':item.html()
            }, url)


        cur_page = response.doc('#J_topPage > span > b').text()
        if 1 == int(cur_page):
            total_pages = response.doc('#J_topPage > span > i').text()
            for index in range(2,int(total_pages) + 1):
                self.crawl('%s&page=%r' %(response.url, index),
                           callback=self.detail_page, fetch_type='js',auto_recrawl=True)


    def on_message(self, project, msg):
        return msg
