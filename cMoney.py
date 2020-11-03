from News import News
import re
import time
from urllib.parse import quote
import string
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from logging.config import fileConfig
import logging


fileConfig('config.ini')
logger = logging.getLogger('Mobile01_By_Search_Log:')


class CMoney(News):
    def __init__(self, stock_num, board='news'):
        super().__init__()
        self.stock_num = stock_num
        self.base_url = 'https://www.cmoney.tw/follow/channel/'
        # self.search_stock_num_url = 'https://www.cmoney.tw/follow/channel/stock-{stock_num}?chart=d&type=Personal'
        self.search_stock_num_url = 'https://www.cmoney.tw/follow/channel/stock-{stock_num}?chart=d&type=Feed'
        self.cookie = 'AspSession=futa5b1wksfp4fpn4iahocsb; ASP.NET_SessionId=bhngstrlmpvrxlljnpecozzx; __asc=4e635de31741f4e27b58d7ecc8d; __auc=4e635de31741f4e27b58d7ecc8d; _ga=GA1.2.1131623218.1598253051; _gid=GA1.2.1603602941.1598253051; _hjid=fdf65d5f-5f49-4286-ab82-cee66a1cc0ce; AviviD_uuid=0609b4cb-03ab-4812-b332-8ee0962c6ce7; webuserid=05926589-5146-4274-57e6-65f220d840bb; _hjAbsoluteSessionInProgress=1; AviviD_already_exist=1; AviviD_show_sub=1; AviviD_refresh_uuid_status=2; AviviD_waterfall_status=0; MemberId=76o0FRWkoW7zz; NoPromptForFbBindingList=,JIjZXGEf8D8jmC9jEERJLJAAz; _gat_real=1; page_view=9; _hjTLDTest=1'
        # self.session = requests.Session()
        # self.response = self.session.get('https://www.cmoney.tw/member/login/')
        self.driver = self.get_driver(self.base_url)
        self.driver.get(self.search_stock_num_url.format(stock_num=stock_num))
        self.wait = WebDriverWait(self.driver, 10, 0.5)
        # wait
        self.wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@id='DivStockInfo']")))
        start_time = time.time()
        while True:
            self.stock_num_driver_soup = self.get_soup_from_selenium(self.driver)
            if (time.time() - start_time) > 10:
                break
            if len(self.stock_num_driver_soup.find('ul', id="DivItemList").find_all('li', id=True)) < 15:
                self.expand_post_for_selenium(self.driver)
            else:
                break
        self.stock_num_driver_soup = self.get_soup_from_selenium(self.driver)
        self.stock_data = self.get_stock_num_data(self.stock_num_driver_soup)
        if board == 'news':
            self.news_data = self.get_stock_num_news_data(self.stock_num_driver_soup)
        elif board == 'comment':
            self.comments_data = self.get_stock_num_comment_data(self.stock_num_driver_soup)

    def get_stock_num_data(self, soup):
        stock_info_list = soup.find('ul', class_="list7").find_all('li')
        stock_data = {
            "股票名稱": soup.find('h1', class_="onestock2-name").text,
            "股價": {self.go_up_or_dw(stock_info_list[0].span.get('class')[0]): stock_info_list[0].text[2:]},
            "漲跌": {self.go_up_or_dw(stock_info_list[1].span.get('class')[0]): stock_info_list[1].text[2:]},
            "漲幅": {self.go_up_or_dw(stock_info_list[2].span.get('class')[0]): stock_info_list[2].text[2:]},
            "成交量": stock_info_list[3].text[3:],
            "股本（百萬）": stock_info_list[4].text[6:],
            "本益比": stock_info_list[5].text[3:],
            "產業": stock_info_list[6].text[2:],
            "權證": stock_info_list[7].text[2:],
        }
        return stock_data

    def get_stock_num_comment_data(self, soup):
        forum_data = {}
        forum_list = soup.find('ul', id="DivItemList").find_all('li', id=True)
        for index, f in enumerate(forum_list):
            try:
                forum_data[str(index)] = {
                    "Stock Name": self.stock_data['股票名稱'],
                    "User Name": f.find('a', class_="member-name ng-scope").text,
                    "Follow Channel": self.get_user_follow_channel(f.find('div', class_="rss-content-doc-hot-middle").find_all('a')),
                    "Content": f.find('div', class_="main-content").text,
                    "Push Time": f.find('div', class_="push-hot-from")['title'],  # 2020/09/07 10:10
                }
            except:
                continue
        return forum_data

    def get_stock_num_news_data(self, soup):
        logger.info(f'Starting get {self.stock_num} stock news data.')
        news_data = {}
        news_list = soup.find('ul', id="DivItemList").find_all('li', id=True)
        for index, news in enumerate(news_list):
            try:
                news_source = news.find('div', class_="rss-content-right-text cardShow").a.text
                news_url = news.find('div', class_="rss-content-doc-hot-middle").a['href']
                news_url = quote(news_url, safe=string.printable)
                try:
                    if 'udn' in news_source or '聯合新聞網' in news_source:
                        news_content = self.get_news_content_from_udn(news_url)
                    elif '經濟日報' in news_source:
                        news_content = self.get_news_content_from_money(news_url)
                    elif 'Yahoo' in news_source:
                        news_content = self.get_news_content_from_yahoo(news_url)
                    elif 'Google' in news_source:
                        news_content = self.get_news_content_from_google(news_url)
                    elif '財經知識庫' in news_source:
                        news_content = self.get_news_content_from_moneydj(news_url)
                    elif '批踢踢' in news_source:
                        news_content = self.get_news_content_from_ptt(news_url)
                    elif 'Mobile01' in news_source:
                        news_content = self.get_news_content_from_mobile01(news_url)
                    elif 'TechNews' in news_source:
                        news_content = self.get_news_content_from_technews(news_url)
                    elif '商周財富網' in news_source:
                        news_content = self.get_news_content_from_businessweekly(news_url)
                    else:
                        news_content = news.find('div', class_="main-content").text
                except:
                    logger.exception(f'STH error when get {news_source} new content(URL: {news_url}).')
                    news_content = news.find('div', class_="main-content").text
                news_data[str(index)] = {
                    "URL": news_url,
                    "Stock Num": self.stock_data['股票名稱'],
                    "Title": news.find('div', class_="rss-content-doc-hot-middle").a.text,
                    "News Source": news_source,
                    "Text": news_content,
                    "Push Time": news.find('div', class_="push-hot-from")['title'],  # 2020/09/07 10:10
                }
                if news_data[str(index)]['Text'] == '':
                    news_data[str(index)]['Text'] = news_data[str(index)]['Title']
            except:
                logger.exception('error 1')
                continue
        logger.info(f'Finished get {self.stock_num} stock news data.')
        return news_data

    def get_news_content_from_udn(self, url):
        cdn_soup = self.get_soup_from_requests(url)
        content_elem = cdn_soup.find('section', itemprop="articleBody").find_all('p')
        content = ''
        for c in content_elem:
            content += c.text
        return content

    def get_news_content_from_money(self, url):
        money_soup = self.get_soup_from_requests(url)
        content_elem = money_soup.find('div', id="article_body").find_all('p')
        content = ''
        for c in content_elem:
            content += c.text
        return content

    def get_news_content_from_yahoo(self, url):
        for try_time in range(3):
            try:
                yahoo_soup = self.get_soup_from_requests(url)
                content_elem = yahoo_soup.find('article', itemprop="articleBody").find_all('p')
                content = ''
                for c in content_elem:
                    content += c.text
            except AttributeError:
                pass
        return content

    def get_news_content_from_google(self, url):
        google_soup = self.get_soup_from_requests(url)
        try:
            content_elem = google_soup.find('div', class_="caas-body").find_all('p')
            content = ''
            for c in content_elem:
                content += c.text
        except AttributeError:
            self.driver.get(url)
            if 'yahoo' in self.driver.current_url:
                content = self.get_news_content_from_yahoo(url)
            elif 'money' in self.driver.current_url:
                content = self.get_news_content_from_money(url)
        return content

    def get_news_content_from_moneydj(self, url):
        moneydj_soup = self.get_soup_from_requests(url)
        content_elem = moneydj_soup.find('article', id="MainContent_Contents_mainArticle").find_all('p')
        content = ''
        for c in content_elem:
            content += c.text
        return content

    def get_news_content_from_ptt(self, url):
        ptt_soup = self.get_soup_from_requests(url)
        content_elem = ptt_soup.find('div', id='main-content')
        content = content_elem.text
        for elem in content_elem.find_all(['span', 'a']):
            content = content.replace(elem.text, '')
        content = content.split('※')[0]
        return content

    def get_news_content_from_mobile01(self, url):
        mobile01_soup = self.get_soup_from_requests(url)
        content_elem = mobile01_soup.find_all('div', class_="l-articlePage")[0]
        content = content_elem.find('div', class_="l-publish__content").find('div', itemprop="articleBody").text.strip()
        return content

    def get_news_content_from_technews(self, url):
        technews_soup = self.get_soup_from_requests(url)
        content_elem = technews_soup.find('div', class_="indent").find_all('p')
        content = ''
        for c in content_elem:
            content += c.text
        return content

    def get_news_content_from_businessweekly(self, url):
        businessweekly_soup = self.get_soup_from_requests(url)
        content_elem = businessweekly_soup.find('div', class_="article_main").find_all('p')
        content = ''
        for c in content_elem:
            content += c.text
        return content

    def get_news_content_from_wearn(self, url):
        wearn_soup = self.get_soup_from_requests(url)
        content_elem = wearn_soup.find('div', id="ctkeywordcontent").find_all('p')
        content = ''
        for c in content_elem:
            content += c.text
        return content

    def go_up_or_dw(self, cls):
        if re.search('up', cls):
            return '正'
        elif re.search('dw', cls):
            return '負'

    def get_user_follow_channel(self, cls_list):
        follow_channel = {}
        for c in cls_list:
            follow_channel[c.text] = c.get('href')
        return follow_channel


# def save_stock_num_data_to_db(stock_data):
#     csd = CMoneyStockData(
#         price=stock_data['股價'],
#         change=stock_data['漲跌'],
#         change_percentage=stock_data['漲幅'],
#         vol=stock_data['成交量'],
#         captial=stock_data['股本（百萬）'],
#         PE_ratio=stock_data['本益比'],
#         industry=stock_data['產業'],
#         warrant=stock_data['權證'],
#     )
#     csd.save()


# def save_stock_num_comments_data_to_db(comments_data):
#     for c_data in comments_data:
#         csc = CmoneyStockComments(
#             stock_name=c_data['Stock Name'],
#             user_name=c_data['User Name'],
#             follow_channel=c_data[''],
#             text=c_data['Content'],
#             created_time=c_data['Push Time'],
#         )
#         csc.save()


def main():
    board = 'news'
    cmoney = CMoney(2330, board=board)
    print(cmoney.stock_data)
    if board == 'news':
        print(cmoney.news_data)
    elif board == 'comment':
        print(cmoney.comments_data)


if __name__ == '__main__':
    main()
