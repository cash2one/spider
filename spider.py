#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2016-05-27 11:13:57
# Project: chaoshi_tmall_com

from pyspider.libs.base_handler import *
import urlparse
import json

class Handler(BaseHandler):
    crawl_config = {
    'itag': 'v1.1',
    'headers': {
    'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'accept-encoding':'gzip, deflate, sdch',
    'accept-language':'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
        'user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
    }
}

    def __init__(self):
        self.resproc = ResponseProcessor()

    @every(minutes=6 * 60)
    def on_start(self):
        self.crawl('https://chaoshi.tmall.com/',  fetch_type='js', callback=self.index_page)

    @config(age=24 * 60 * 60)
    def index_page(self, response):
        for each in response.doc('a[href^="https://list.tmall.com/search_product.htm"]').items():
            self.crawl(each.attr.href, callback=self.list_page)


    @config(age=6 * 60 * 60)
    def list_page(self, response):
        page_len = response.doc('input[name="totalPage"]').attr.value
        #cur_page = response.doc('input[name="jumpto"]').attr.value
        url_info = urlparse.urlparse(response.url)
        url_query = url_info.query
        queries = urlparse.parse_qs(url_query)
        self.has_upper_list = False
        kinds_count = len(response.doc('#J_Tree > li'))
        for each in response.doc('#J_Tree > li > a[href^="https://list.tmall.com/search_product.htm"]').items():
            self.crawl(each.attr['href'], callback=self.list_page)
            self.has_upper_list = True

        #如果没有上级分类 ; 或则当前类别下商品已经超过50页。则翻页
        print "%s %s" %(self.has_upper_list,page_len)
        if (not self.has_upper_list) or (int(page_len) > 30):
            if not queries.has_key('s'):
                for i in range(1, int(page_len)):
                    self.crawl("%s&s=%r" %(response.url,i*40), callback=self.list_page)


        return self.resproc.process(response, self)


class ResponseProcessor:
    def __init__(self):
        self.result = {};

    def _build_product(self):
        product_info = {}
        product_info["product_id"] = self.product_id
        product_info['product_atp'] = self.product_atp
        product_info['product_img_url'] = self.product_img_url
        product_info['product_price'] = self.product_price
        product_info['product_title'] = self.product_title
        product_info['product_url'] = self.product_url
        product_info['product_shop'] = {
            'name':self.product_shop_name,
            'url':self.product_shop_url,
        }
        product_info['product_status'] = {
            'sales_month':self.product_status_sales_month,
            'sales_total':self.product_status_sales_total,
            'comment_url':self.product_status_comment_url,
            'comment_num':self.product_status_comment_num,
        }
        self.result["product_list"].append(product_info)

    def process(self, response, handler):
        self.result["url"] = response.url
        self.result["title"] = response.doc('title').text()
        self.result["product_list"] = []


        self.product_list = response.doc('#J_ItemList')
        if  self.product_list:
            self.result["count"] = len(response.doc('#J_ItemList > div.product'))
            for each in response.doc('#J_ItemList > div.product').items():
                self.product_id = each.attr['data-id']
                self.product_atp = each.attr['data-atp']
                self.product_img = each('div.product-iWrap div.productImg-wrap a.productImg img')
                self.product_img_url = self.product_img.attr['src']
                self.product_price = each('div.product-iWrap p.productPrice em').attr['title']
                self.product_title  = each('div.product-iWrap p.productTitle a').attr['title']
                self.product_url  = each('div.product-iWrap p.productTitle a').attr['href']
                self.product_shop = each('div.product-iWrap div.productShop')
                self.product_shop_name = self.product_shop('a.productShop-name').text()
                self.product_shop_url = self.product_shop('a.productShop-name').attr['href']
                self.product_status = each('div.product-iWrap p.productStatus')
                self.product_status_sales_month = self.product_status('span:nth-child(1) em').text()
                self.product_status_comment_url = self.product_status('span:nth-child(2) a').attr['href']
                self.product_status_comment_num = self.product_status('span:nth-child(2) a').text()
                self.product_status_sales_total = ''

                self._build_product()
        else:
            self.product_list = response.doc('#J_ProductList')
            if self.product_list:
                self.result["count"] = len(response.doc('#J_ProductList > li.product'))
                for each in response.doc('#J_ProductList > li.product').items():
                    self.product_id = each.attr['data-itemid']
                    self.product_atp = ''
                    self.product_img = each('div.productInfo div.product-img a img')
                    self.product_img_url = self.product_img.attr['data-ks-lazyload']
                    self.product_price = each('div.productInfo div.item-summary div.item-price span.ui-price strong').text()
                    self.product_title  = each('div.productInfo .product-title a').text()
                    self.product_url  = each('div.productInfo .product-title a').attr['href']
                    self.product_shop = ''
                    self.product_shop_name = ''
                    self.product_shop_url = ''
                    self.product_status = each('div.productInfo div.item-summary')
                    self.product_status_sales_total = self.product_status('div.item-sum strong').text()
                    self.product_status_sales_month = ''
                    self.product_status_comment_url = ''
                    self.product_status_comment_num = ''
                    self._build_product()

        return json.dumps(self.result)
