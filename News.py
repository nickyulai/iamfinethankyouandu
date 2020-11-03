import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import datetime
import re
from logging.config import fileConfig
import logging
import json
import time
import math
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
# from news.models import EtTodayNews, AppleDailyNews, YahooNews, EBCNews, TVBSNews, SETNNews, LTNNews, MoneyNews
# from mushishi import mynlp, newsbot
# from django.http import HttpResponseRedirect
# from mushishi.wordcloud import news_phrase
# from mushishi.models import KeywordList

fileConfig('config.ini')
logger = logging.getLogger('News_Log:')
requests.adapters.DEFAULT_RETRIES = 5


class News:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
            'Connection': 'close',
        }

    def get_soup_from_requests(self, url=None):
        r = requests.get(url, headers=self.headers)
        return BeautifulSoup(r.text, 'lxml')

    @staticmethod
    def get_soup_from_selenium(driver=None):
        return BeautifulSoup(driver.page_source, 'lxml')

    @staticmethod
    def get_driver(url=None):
        options = Options()
        # options.add_argument('--headless')
        # options.add_argument('blink-settings=imagesEnabled=false')
        driver = webdriver.Chrome(chrome_options=options)
        driver.get(url=url)
        return driver

    # @staticmethod
    def get_soup_from_requests_with_cookie(self, url=None, cookie=None):
        r = requests.get(url, headers=self.headers, cookies=cookie)
        return BeautifulSoup(r.text, 'lxml')
    # @staticmethod
    # def get_keyword_count(content):
    #     keyword_count = 0
    #     for lst in KeywordList.objects.filter(actived=True).values_list('keyword', flat=True).distinct():
    #         for k in lst:
    #             try:
    #                 keyword_count += news_phrase(content).count_words[k]
    #             except KeyError:
    #                 pass
    #     return keyword_count

    @staticmethod
    def expand_post_for_selenium(driver=None):
        driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")

    @staticmethod
    def convert_time_from_minutes_or_hours(date_time):
        if re.search(r'分鐘', date_time):
            time_convert = datetime.datetime.now(
            ) - datetime.timedelta(minutes=int(re.search(r'\d+', date_time).group()))
        elif re.search(r'小時前', date_time):
            time_convert = datetime.datetime.now(
            ) - datetime.timedelta(hours=int(re.search(r'\d+', date_time).group()))
        else:
            return date_time
        return time_convert


class EtToday(News):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://www.ettoday.net'
        self.newest_news_url = 'https://www.ettoday.net/news/news-list.htm'
        self.search_news = 'https://www.ettoday.net/news_search/doSearch.php?keywords={search_name}'

    def get_ettoday_news(self):
        logger.info(f'Starting get {self.__class__.__name__} Newest News.')
        the_newest_news_soup = self.get_soup_from_requests(
            self.newest_news_url)
        the_newest_news = the_newest_news_soup.find(
            'div', class_="part_list_2").find_all('h3')
        for news in the_newest_news:
            news_href = news.find('a').get('href')
            # db url duplitcate
            # if EtTodayNews.objects.filter(url=f'{self.base_url}{news_href}'):
            #     continue
            date_time = news.find('span', class_="date").text
            news_type = news.find('em').text
            news_title = news.find('a').text
            news_content = self.get_news_content(f'{self.base_url}{news_href}')
            # nlp_tag = mynlp.content_nlp(news_content)
            logger.debug(f'News Title: {news_title} \n News Type: {news_type} News Created Time: {date_time} \n'
                         f'News URL: {self.base_url}{news_href} \n News Content: {news_content}')
            # keyword count
            # keyword_count = self.get_keyword_count(news_content)
            # etn = EtTodayNews(
            #     url=f'{self.base_url}{news_href}',
            #     news_type=news_type,
            #     title=news_title,
            #     text=news_content,
            #     created_time=datetime.datetime.strptime(
            #         date_time, '%Y/%m/%d %H:%M'),
            #     nlp_tag=nlp_tag,
            #     pushed=0,
            #     keyword_count=keyword_count,
            # )
            # etn.save()
            # newsbot.message2bot_by_news(
            #     'ETToday', f'{self.base_url}{news_href}')
        logger.info(f'Finished get {self.__class__.__name__} Newest News.')

    def get_news_content(self, url):
        content_soup = self.get_soup_from_requests(url)
        news_story = content_soup.find('div', class_="story").find_all('p')
        content = ''
        for c in news_story:
            content += c.text
        return content

    def get_news_by_search(self, search_name, since_date='2020-07-29', until_date='2020-08-22'):
        logger.info(f'Starting get {self.__class__.__name__} Search News.')
        search_field_soup = self.get_soup_from_requests(
            self.search_news.format(search_name=quote(search_name)))
        page_count = re.search(
            r'\d+', search_field_soup.find('p', class_="info").text.split('|')[1]).group()
        page_url = '&idx=1&page={page_count}'
        for page in range(int(page_count)):
            news_page_soup = self.get_soup_from_requests(f'{self.search_news.format(search_name=quote(search_name))}{page_url.format(page_count=page)}')
            news_list = news_page_soup.find('div', class_="result_archive").find_all(
                'div', class_="archive clearfix")
            for news in news_list:
                try:
                    news_href = news.find('a').get('href')
                    news_title = news.find('h2').a.text
                    news_type, date_time = re.search(
                        r'\((...)+\d+-\d+-\d+ \d+:\d+\)', news.find('p').text).group().split('/')
                    created_time = datetime.datetime.strptime(
                        date_time[1:-1], "%Y-%m-%d %H:%M")
                    if datetime.datetime.strptime(since_date, "%Y-%m-%d") > created_time:
                        break
                    elif created_time > datetime.datetime.strptime(until_date, "%Y-%m-%d"):
                        continue
                    news_content = self.get_news_content(news_href)
                    # nlp_tag = mynlp.content_nlp(news_content)
                    logger.debug(
                        f'News Title: {news_title} \n '
                        f'News Type: {news_type[1:-1]} News Created Time: {date_time[1:-1]} \n'
                        f'News URL: {news_href} \n News Content: {news_content}')
                    # keyword count
                    # etn = EtTodayNews(
                    #     url=news_href,
                    #     news_type=news_type[1:-1],
                    #     title=news_title,
                    #     text=news_content,
                    #     created_time=created_time,
                    #     nlp_tag=nlp_tag,
                    #     pushed=-1,
                    # )
                    # etn.save()
                except:
                    logger.exception(f'{news_href}')
                    continue
        logger.info(f'Finished get {self.__class__.__name__} Search News.')


class AppleDaily(News):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://tw.appledaily.com'
        self.newest_news_url = 'https://tw.appledaily.com/realtime/new/'
        self.driver = self.get_driver(self.base_url)
        self.wait = WebDriverWait(self.driver, 10, 0.5)
        self.search_url = 'https://tw.appledaily.com/pf/api/v3/content/fetch/search-query?query=%7B%22searchTerm%22%3A%22{search_name}%22%2C%22start%22%3A{num}%7D&d=127&_website=tw-appledaily'

    def get_apple_daily_news(self):
        logger.info(f'Starting get {self.__class__.__name__} Newest News.')
        self.driver.get(self.newest_news_url)
        soup = self.get_soup_from_selenium(self.driver)
        the_newest_news_list = soup.find_all('div', class_="flex-feature")
        try:
            for news in the_newest_news_list:
                news_href = news.find('a').get('href')
                # if AppleDailyNews.objects.filter(url=f'{self.base_url}{news_href}'):
                #     continue
                news_type = news_href.split('/')[1]
                news_title = news.find('span', class_=True).text
                date_time = news.find('div', class_="timestamp").text
                news_content, time_stamp = self.get_news_content(
                    f'{self.base_url}{news_href}')
                # nlp_tag = mynlp.content_nlp(news_content)
                logger.debug(
                    f'News Title: {news_title} News Type: {news_type} \n'
                    f'News URL: {self.base_url}{news_href} News Date Time: {date_time} \n'
                    f'News Content: {news_content}')
                # keyword count
                # keyword_count = self.get_keyword_count(news_content)
                # adn = AppleDailyNews(
                #     url=f'{self.base_url}{news_href}',
                #     news_type=news_type,
                #     title=news_title,
                #     text=news_content,
                #     created_time=datetime.datetime.strptime(
                #         date_time.split(': ')[2], '%Y/%m/%d %H:%M'),
                #     nlp_tag=nlp_tag,
                #     pushed=0,
                #     keyword_count=keyword_count,
                # )
                # adn.save()
                # newsbot.message2bot_by_news(
                #     'AppleDaily', f'{self.base_url}{news_href}')
        except:
            logger.exception('Somrthing error when get appledaily news')
        finally:
            self.driver.quit()
        logger.info(f'Finished get {self.__class__.__name__} Newest News.')

    def get_news_content(self, url):
        self.driver.get(url)
        try:
            self.driver.execute_script("window.scrollTo(0,1000)")
            self.wait.until(EC.visibility_of_element_located(
                (By.CSS_SELECTOR, ".text--desktop > span")))
            self.wait.until(
                EC.visibility_of_all_elements_located((By.XPATH, "//div[@id='articleBody']/section[2]/div[3]/span")))
        except:
            pass
        content_soup = self.get_soup_from_selenium(self.driver)
        content = ''
        try:
            content = content_soup.find(
                'div', class_="article_body").find('p').text
        except AttributeError:
            logger.warning(f'{url} does not find p text.')
            pass
        try:
            content_elem = content_soup.find(
                'div', class_="article_body").find_all('span')
        except:
            logger.exception(f'something error when get {url} span text')
            return
        for c in content_elem:
            content += c.text
        time_stamp = content_soup.find('div', class_="timestamp").text
        try:
            time_convert = time_stamp.split('： ')[1]
        except IndexError:
            time_convert = self.convert_time_from_minutes_or_hours(time_stamp)
        except:
            logger.exception(
                f'Apple daily {url} get content created time fail.')
            time_convert = ''
        return content, time_convert

    def get_news_by_search(self, search_name, since_date='2018-01-01', until_date='2022-12-31'):
        logger.info(f'Starting get {self.__class__.__name__} Search News.')
        news_num = 0
        while True:
            try:
                search_soup = self.get_soup_from_requests(self.search_url.format(search_name=search_name, num=news_num))
                news_list = json.loads(search_soup.find('p').text)['content']
                if len(news_list) == 0:
                    break
                for news in news_list:
                    news_href = news['sharing']['url']
                    news_title = news['title']
                    news_type = news['brandCategoryName']
                    news_pub_time = datetime.datetime.fromtimestamp(int(news['pubDate']))
                    if datetime.datetime.strptime(since_date, "%Y-%m-%d") > news_pub_time:
                        break
                    elif news_pub_time > datetime.datetime.strptime(until_date, "%Y-%m-%d"):
                        continue
                    try:
                        news_content, date_time = self.get_news_content(news_href)
                    except:
                        continue
                    # nlp_tag = mynlp.content_nlp(news_content)
                    logger.debug(
                        f'News Title: {news_title} News Type: {news_type} \n'
                        f'News URL: {news_href} News Date Time: {date_time} \n'
                        f'News Content: {news_content}')
                    # adn = AppleDailyNews(
                    #     url=news_href,
                    #     news_type=news_type,
                    #     title=news_title,
                    #     text=news_content,
                    #     created_time=news_pub_time,
                    #     nlp_tag=nlp_tag,
                    #     pushed=-1,
                    # )
                    # adn.save()
                news_num += 20
            except:
                logger.exception('Something error when get appledaily search news.')
                break
        logger.info(f'Finished get {self.__class__.__name__} Search News.')


class Yahoo(News):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://tw.news.yahoo.com/'
        self.news_board = {'首頁': '/', '政治': 'politics', '財經': 'finance', '娛樂': 'entertainment',
                           '運動': 'sports', '社會地方': 'society', '國際': 'world', '生活': 'lifestyle', '健康': 'health',
                           '科技': 'technology', }
        self.search_url = 'https://tw.news.yahoo.com/search?p={search_name}'

    def get_yahoo_news(self):
        logger.info(f'Starting get {self.__class__.__name__} Newest News.')
        for board in self.news_board:
            news_board_url = f'{self.base_url}{self.news_board[board]}'
            the_news_soup = self.get_soup_from_requests(news_board_url)
            try:
                the_news_list = the_news_soup.find(
                    'ul', class_="H(100%) D(ib) Mstart(24px) W(32.7%)").find_all('li')
            except AttributeError:
                logger.exception(f'{board} get soup fail.')
                continue
            for news in the_news_list:
                try:
                    news_href = news.find('a').get('href')
                    # if YahooNews.objects.filter(url=news_href):
                    #     continue
                    news_title = news.find('a').text
                    date_time, news_content = self.get_news_content(news_href)
                    # nlp_tag = mynlp.content_nlp(news_content)
                    logger.debug(
                        f'News Title: {news_title} News Type: {board}\n'
                        f'News URL: {news_href} News Date Time: {date_time} \n'
                        f'News Content: {news_content}')
                    # keyword count
                    keyword_count = self.get_keyword_count(news_content)
                    # yhn = YahooNews(
                    #     url=news_href,
                    #     news_type=board,
                    #     title=news_title,
                    #     text=news_content,
                    #     created_time=date_time,
                    #     nlp_tag=nlp_tag,
                    #     pushed=0,
                    #     keyword_count=keyword_count,
                    # )
                    # yhn.save()
                    # newsbot.message2bot_by_news('Yahoo', news_href)
                except:
                    logger.exception(
                        f'Get Yahoo! {board} News({news_href}) Fail.')
                    continue
        logger.info(f'Finished get {self.__class__.__name__} Newest News.')

    def get_news_content(self, url):
        the_news_content_soup = self.get_soup_from_requests(url)
        try:
            date_time = the_news_content_soup.find('time').get('datetime')
        except AttributeError:  # get date time from health board
            date_time = the_news_content_soup.find(
                'div', class_="date").text.split(' ')[0]
            date_time = datetime.datetime.strptime(date_time, "%Y-%m-%d")
            pass
        except:
            logger.exception(f'({url}) is AD or Video ot sth')
            return '', ''
        content_elem = the_news_content_soup.find_all('p', text=True)
        content = ''
        for c in content_elem:
            content += c.text
        return date_time, content

    def get_news_by_search(self, search_name, since_date='2020-01-01', until_date='2022-12-31'):
        logger.info(f'Starting get {self.__class__.__name__} Search News.')
        yahoo_driver = self.get_driver(self.base_url)
        yahoo_driver.get(self.search_url.format(search_name=quote(search_name)))
        start_time = time.time()
        while True:
            search_soup = self.get_soup_from_selenium(driver=yahoo_driver)
            news_list = search_soup.find('ul', id="stream-container-scroll-template").find_all('li')
            last_post_time = news_list[-1].find('div', class_="C(#959595) Fz(13px) C(#1e7d83) Fw(n)! Mend(14px)! D(ib) Mb(6px)").text.split(' • ')[1]
            last_time = self.convert_datetime(last_post_time)
            if last_time < datetime.datetime.strptime(since_date, "%Y-%m-%d"):
                break
            if time.time() - start_time > 10:
                break
            self.expand_post_for_selenium(yahoo_driver)
        # search_soup = self.get_soup_from_requests(search_url)
        for news in news_list:
            news_href = news.a.get('href')
            news_title = news.find('a', href=True).text
            news_type, created_time = news.find('div', class_="C(#959595) Fz(13px) C(#1e7d83) Fw(n)! Mend(14px)! D(ib) Mb(6px)").text.split(' • ')
            date_time, news_content = self.get_news_content(f'{self.base_url}{news_href}')
            # nlp_tag = mynlp.content_nlp(news_content)
            logger.debug(
                f'News Title: {news_title} News Type: {news_type} \n'
                f'News URL: {self.base_url}{news_href} News Date Time: {date_time} \n'
                f'News Content: {news_content}')
            # yhn = YahooNews(
            #     url=news_href,
            #     news_type=news_type,
            #     title=news_title,
            #     text=news_content,
            #     created_time=date_time,
            #     nlp_tag=nlp_tag,
            #     pushed=0,
            # )
            # yhn.save()
        logger.info(f'Finished get {self.__class__.__name__} Search News.')

    def convert_datetime(self, last_time):
        if re.search(r'天前', last_time):
            return datetime.datetime.today() - datetime.timedelta(days=int(re.search(r'\d+', last_time).group()))
        elif re.search(r'年', last_time):
            return datetime.datetime.strptime(last_time.split(' ')[0], "%Y年%m月%d日")
        else:
            return datetime.datetime.today()


class EBC(News):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://news.ebc.net.tw'
        self.newest_news_url = 'https://news.ebc.net.tw/realtime?page={page}'
        self.search_url = 'https://news.ebc.net.tw/Search/Result?type=keyword&value={search_name}&page={page}'

    def get_ebc_news(self):
        logger.info(f'Starting get {self.__class__.__name__} Newest News.')
        for page in (1, 6):  # there are 30 news in a page
            the_newest_news_soup = self.get_soup_from_requests(
                self.newest_news_url.format(page=page))
            news_list = the_newest_news_soup.find(
                'div', class_="news-list-box").find_all('div', class_="style1 white-box")
            for news in news_list:
                news_href = news.a.get('href')  # '/news/business/218643'
                # if EBCNews.objects.filter(url=f'{self.base_url}{news_href}'):
                #     continue
                news_title = news.find('div', class_="title").text
                date_time = news.find(
                    'span', class_="small-gray-text").text  # '07/16 17:41'
                news_type = news_href.split('/')[2]
                news_content = self.get_news_content(
                    f'{self.base_url}{news_href}')
                # nlp_tag = mynlp.content_nlp(news_content)
                logger.debug(
                    f'News Title: {news_title} News Type: {news_type}\n'
                    f'News URL: {self.base_url}{news_href} News Date Time: {date_time} \n'
                    f'News Content: {news_content}')
                # keyword count
                keyword_count = self.get_keyword_count(news_content)
                # en = EBCNews(
                #     url=f'{self.base_url}{news_href}',
                #     news_type=news_type,
                #     title=news_title,
                #     text=news_content,
                #     created_time=datetime.datetime.strptime(
                #         f'{datetime.datetime.now().year}/{date_time}', '%Y/%m/%d %H:%M'),
                #     nlp_tag=nlp_tag,
                #     pushed=0,
                #     keyword_count=keyword_count,
                # )
                # en.save()
                # newsbot.message2bot_by_news(
                #     'EBC', f'{self.base_url}{news_href}')
        logger.info(f'Finished get {self.__class__.__name__} Newest News.')

    def get_news_content(self, url):
        content = ''
        content_soup = self.get_soup_from_requests(url)
        try:
            content_elem = content_soup.find(
                'span', {'data-reactroot': True}).find_all('p')
            for c in content_elem:
                content += c.text
        except:
            logger.exception(f'EBC News: {url} get content fail.')

        return content

    def get_news_by_search(self, search_name, since_date='2020-01-01', until_date='2022-12-31'):
        logger.info(f'Starting get {self.__class__.__name__} Search News.')
        for page in range(1, 20):
            try:
                search_soup = self.get_soup_from_requests(
                    self.search_url.format(search_name=search_name, page=page))
                news_list = search_soup.find(
                    'div', class_="news-list-box").find_all('div', class_="style1 white-box")
                for news in news_list:
                    date_time = news.find(
                        'span', class_="small-gray-text").text  # '07/16 17:41'
                    try:
                        judge_time = datetime.datetime.strptime(
                            date_time, "%m/%d %H:%M")
                    except:
                        judge_time = datetime.datetime.strptime(
                            date_time, "%Y/%m/%d %H:%M")
                    if judge_time < datetime.datetime.strptime(since_date, "%Y-%m-%d"):
                        return
                    elif judge_time > datetime.datetime.strptime(until_date, "%Y-%m-%d"):
                        continue
                    news_href = news.a.get('href')  # '/news/business/218643'
                    news_title = news.find('div', class_="title").text
                    news_type = news_href.split('/')[2]
                    news_content = self.get_news_content(
                        f'{self.base_url}{news_href}')
                    # nlp_tag = mynlp.content_nlp(news_content)
                    logger.debug(
                        f'News Title: {news_title} News Type: {news_type}\n'
                        f'News URL: {self.base_url}{news_href} News Date Time: {date_time} \n'
                        f'News Content: {news_content}')
                    # en = EBCNews(
                    #     url=f'{self.base_url}{news_href}',
                    #     news_type=news_type,
                    #     title=news_title,
                    #     text=news_content,
                    #     created_time=judge_time,
                    #     nlp_tag=nlp_tag,
                    #     pushed=-1,
                    # )
                    # en.save()
            except:
                logger.exception('Maybe error when get ebc news search.')
                break
        logger.info(f'Finished get {self.__class__.__name__} Search News.')


class TVBS(News):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://news.tvbs.com.tw'
        self.search_url = 'https://news.tvbs.com.tw/news/searchresult/news/{page}/?search_text={search_name}'

    def get_tvbs_news(self):
        logger.info(f'Starting get {self.__class__.__name__} Newest News.')
        the_newest_news_soup = self.get_soup_from_requests(self.base_url)
        first_list = the_newest_news_soup.find(
            'div', class_="real_time_box").ul.find_all('li', recursive=False)
        for news_list in first_list:
            second_list = news_list.ul.find_all('li')
            for news in second_list:
                news_href = news.a.get('href')
                # if TVBSNews.objects.filter(url=f'{self.base_url}{news_href}'):
                #     continue
                news_title = news.find('h2', class_="txt").text
                news_type = news_href.split('/')[1]
                date_time = news.find('div', class_="icon_time time").text
                convert_time = self.convert_time_from_minutes_or_hours(date_time)
                news_content = self.get_news_content(
                    f'{self.base_url}{news_href}')
                # nlp_tag = mynlp.content_nlp(news_content)
                logger.debug(
                    f'News Title: {news_title} News Type: {news_type}\n'
                    f'News URL: {self.base_url}{news_href} News Date Time: {convert_time} \n'
                    f'News Content: {news_content}')
                # keyword count
                # keyword_count = self.get_keyword_count(news_content)
                # tn = TVBSNews(
                #     url=f'{self.base_url}{news_href}',
                #     news_type=news_type,
                #     title=news_title,
                #     text=news_content,
                #     created_time=datetime.datetime.strptime(
                #         date_time, '%Y/%m/%d %H:%M'),
                #     nlp_tag=nlp_tag,
                #     pushed=0,
                #     keyword_count=keyword_count,
                # )
                # tn.save()
                # newsbot.message2bot_by_news(
                #     'TVBS', f'{self.base_url}{news_href}')
        logger.info(f'Finished get {self.__class__.__name__} Newest News.')

    def get_news_content(self, url):
        content = ''
        content_soup = self.get_soup_from_requests(url)
        story = content_soup.find('div', id="news_detail_div")
        try:
            content += story.find('p').text
        except:
            pass
        try:
            content_elem = story.find_all(text=True, recursive=False)
            for c in content_elem[3:]:
                content += c
        except:
            logger.exception(f'TVBS News: {url} get content fail.')
            pass

        return content

    def get_news_by_search(self, search_name, since_date='2020-01-01', until_date='2022-12-31'):
        logger.info(f'Starting get {self.__class__.__name__} Search News.')
        first_page_soup = self.get_soup_from_requests(
            self.search_url.format(page=1, search_name=quote(search_name)))
        news_count = re.search(
            r'\d+', first_page_soup.find('div', class_="search_list_result").text).group()
        page = 1
        while page <= math.ceil(int(news_count) / 25):
            search_soup = self.get_soup_from_requests(
                self.search_url.format(page=page, search_name=quote(search_name)))
            news_list = search_soup.find(
                'div', class_="search_list_div").find_all('li')
            for news in news_list:
                # '2020/07/21 13:16'
                date_time = news.find('div', class_="icon_time").text
                judge_time = datetime.datetime.strptime(
                    date_time[-16:], "%Y/%m/%d %H:%M")
                if judge_time < datetime.datetime.strptime(since_date, "%Y-%m-%d") < judge_time:
                    continue
                # 'https://news.tvbs.com.tw/news/search_check/news/1357429'
                href = news.a.get('href')
                news_title = news.find('div', class_="search_list_txt").text
                news_content = self.get_news_content(href)
                # nlp_tag = mynlp.content_nlp(news_content)
                logger.debug(
                    f'News Title: {news_title} News Type: search_news \n'
                    f'News URL: {href} News Date Time: {judge_time} \n'
                    f'News Content: {news_content}')
                # tn = TVBSNews(
                #     url=news_href,
                #     news_type=news_type,
                #     title=news_title,
                #     text=news_content,
                #     created_time=datetime.datetime.strptime(
                #         date_time, '%Y/%m/%d %H:%M'),
                #     nlp_tag=nlp_tag,
                #     pushed=-1,
                # )
                # tn.save()
            page += 1
        logger.info(f'Finished get {self.__class__.__name__} Search News.')


class SETN(News):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://www.setn.com'
        self.newest_news_url = 'https://www.setn.com/ViewAll.aspx?p={page}'
        self.search_url = 'https://www.setn.com/search.aspx?q={search_name}&p={page}'

    def get_setn_news(self):
        logger.info(f'Starting get {self.__class__.__name__} Newest News.')
        for page in range(1, 4):
            the_newest_news_soup = self.get_soup_from_requests(
                self.newest_news_url.format(page=page))
            news_list = the_newest_news_soup.find(
                'div', class_="row NewsList").find_all('div', recursive=False)
            for news in news_list:
                news_href = news.find('a', class_="gt").get('href')
                # if SETNNews.objects.filter(url=f'{self.base_url}{news_href}'):
                #     continue
                news_title = news.find('h3', class_="view-li-title").text
                news_type = news.a.text
                date_time = news.time.text  # '07/23 12:10'
                news_content = self.get_news_content(
                    f'{self.base_url}{news_href}')
                # nlp_tag = mynlp.content_nlp(news_content)
                logger.debug(
                    f'News Title: {news_title} News Type: {news_type} \n'
                    f'News URL: {self.base_url}{news_href} News Date Time: {date_time} \n'
                    f'News Content: {news_content}')
                # keyword count
                # keyword_count = self.get_keyword_count(news_content)
                # sn = SETNNews(
                #     url=f'{self.base_url}{news_href}',
                #     news_type=news_type,
                #     title=news_title,
                #     text=news_content,
                #     created_time=datetime.datetime.strptime(
                #         f'{datetime.datetime.now().year}/{date_time}', '%Y/%m/%d %H:%M'),
                #     nlp_tag=nlp_tag,
                #     pushed=0,
                #     keyword_count=keyword_count,
                # )
                # sn.save()
                # newsbot.message2bot_by_news(
                #     'SETN', f'{self.base_url}{news_href}')
                time.sleep(5)
        logger.info(f'Finished get {self.__class__.__name__} Newest News.')

    def get_news_content(self, url):
        try:
            content_soup = self.get_soup_from_requests(url)
        except:
            logger.info(
                f'Get {url} requests fail beacause other side server refuse.')
            return ''
        story = content_soup.find('div', id='Content1')
        if story is None:
            story = content_soup.find('div', itemprop="articleBody")
        content_elem = story.find_all('p', text=True, recursive=False)
        content = ''.join([c.text for c in content_elem])

        return content

    def get_news_by_search(self, search_name, since_date='2020-01-01', until_date='2022-12-31'):
        logger.info(f'Starting get {self.__class__.__name__} Search News.')
        page = 1
        while True:
            try:
                search_soup = self.get_soup_from_requests(
                    self.search_url.format(search_name=quote(search_name), page=page))
                news_list = search_soup.find_all('div', class_="col-lg-4 col-sm-6")
                if len(news_list) == 0:
                    break
                for news in news_list:
                    # '2020/08/05 10:39'
                    date_time = news.find('div', class_="newsimg-date").text
                    judge_time = datetime.datetime.strptime(
                        date_time, "%Y/%m/%d %H:%M")
                    if judge_time < datetime.datetime.strptime(since_date, "%Y-%m-%d"):
                        break
                    elif judge_time > datetime.datetime.strptime(until_date, "%Y-%m-%d"):
                        continue
                    news_href = news.a.get("href")
                    news_title = news.img.get("alt")
                    news_type = news.find('div', class_="newslabel-tab").text
                    news_content = self.get_news_content(
                        f'{self.base_url}/{news_href}')
                    # nlp_tag = mynlp.content_nlp(news_content)
                    logger.debug(
                        f'News Title: {news_title} News Type: {news_type} \n'
                        f'News URL: {self.base_url}/{news_href} News Date Time: {date_time} \n'
                        f'News Content: {news_content}')
                    # sn = SETNNews(
                    #     url=f'{self.base_url}{news_href}',
                    #     news_type=news_type,
                    #     title=news_title,
                    #     text=news_content,
                    #     created_time=datetime.datetime.strptime(
                    #         date_time, '%Y/%m/%d %H:%M'),
                    #     nlp_tag=nlp_tag,
                    #     pushed=-1,
                    # )
                    # sn.save()
                    time.sleep(5)
                page += 1
            except:
                break
        logger.info(f'Finished get {self.__class__.__name__} Search News.')


class LTN(News):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://www.ltn.com.tw'
        self.newest_news_url = 'https://news.ltn.com.tw/list/breakingnews'
        self.search_url = 'https://news.ltn.com.tw/search?keyword={search_name}'
        self.newest_ajax_news_url = 'https://news.ltn.com.tw/ajax/breakingnews/all/{page}'
        self.news_num = 20

    def get_ltn_news(self):
        logger.info(f'Starting get {self.__class__.__name__} Newest News.')
        news_num = 20
        for page in range(1, 6):
            the_newest_news_soup = self.get_soup_from_requests(
                self.newest_ajax_news_url.format(page=page))
            news_json = json.loads(the_newest_news_soup.p.text)
            news_list = news_json['data']
            if page == 1:
                for news in news_list:
                    self.get_news_info_and_save_to_db(news)
            else:
                for i in range(20):
                    self.get_news_info_and_save_to_db(
                        news_list[f'{self.news_num}'])
                    self.news_num += 1
        logger.info(f'Finished get {self.__class__.__name__} Newest News.')

    def get_news_info_and_save_to_db(self, news_list):
        news_href = news_list['url']
        # if LTNNews.objects.filter(url=news_href):
        #     return
        news_title = news_list['title']
        news_type_en, news_type_cn = news_list['type_en'], news_list['type_cn']
        date_time = news_list['time']  # '15:07'
        if re.search(r'\d+-\d+-\d', date_time):
            pass
        news_content = self.get_news_content(news_href)
        # nlp_tag = mynlp.content_nlp(news_content)
        logger.debug(
            f'News Title: {news_title} News Type: {news_type_en} \n'
            f'News URL: {news_href} News Date Time: {date_time} \n'
            f'News Content: {news_content}')
        # keyword count
        # keyword_count = self.get_keyword_count(news_content)
        # ln = LTNNews(
        #     url=news_href,
        #     news_type=news_type_en,
        #     title=news_title,
        #     text=news_content,
        #     created_time=datetime.datetime.strptime(
        #         f'{str(datetime.date.today())} {date_time}', '%Y-%m-%d %H:%M'),
        #     nlp_tag=nlp_tag,
        #     pushed=0,
        #     keyword_count=keyword_count,
        # )
        # ln.save()
        # newsbot.message2bot_by_news('LTN', news_href)

    def get_news_content(self, url):
        content_soup = self.get_soup_from_requests(url)
        try:
            story = content_soup.find('div', class_='text boxTitle boxText')
            if story is None:
                story = content_soup.find('div', class_='text')
            if story is None:
                story = content_soup.find('div', itemprop='articleBody')
            content_elem = story.find_all('p', text=True, recursive=False)
            useless_content = story.find_all('strong', text=True)
            content = ''.join([c.text for c in content_elem])
            for useless in useless_content:
                content = content.replace(useless.text, '')
        except:
            logger.exception('')
            content = ''

        return content

    def get_news_by_search(self, search_name, since_date='2020-01-01', until_date='2020-08-31'):
        logger.info(f'Starting get {self.__class__.__name__} Search News.')
        middle_date = since_date
        page = 1
        while True:
            if (datetime.datetime.strptime(until_date, "%Y-%m-%d") - datetime.datetime.strptime(middle_date,
                                                                                                "%Y-%m-%d")).days > 90:
                middle_date = datetime.datetime.strftime(
                    datetime.datetime.strptime(until_date, "%Y-%m-%d") - datetime.timedelta(days=90), "%Y-%m-%d")
            elif (datetime.datetime.strptime(until_date, "%Y-%m-%d") - datetime.datetime.strptime(middle_date,
                                                                                                  "%Y-%m-%d")).days <= 0:
                break
            while True:
                search_soup = self.get_soup_from_requests(
                    self.search_url.format(search_name=quote(search_name), since_date=middle_date,
                                           until_date=until_date,
                                           page=page))
                try:
                    if search_soup.find('div', class_="snone").p.text == '查無新聞！！':  # out of page
                        break
                except:
                    pass
                news_list = search_soup.find(
                    'ul', class_="searchlist boxTitle").find_all('li')
                for news in news_list:
                    date_time = news.span.text  # '2020-07-19 01:03'
                    try:
                        judge_time = datetime.datetime.strptime(
                            date_time, "%Y-%m-%d %H:%M")
                    except:
                        judge_time = datetime.datetime.strptime(
                            date_time, "%Y-%m-%d")
                    if judge_time < datetime.datetime.strptime(since_date, "%Y-%m-%d"):
                        return
                    elif judge_time > datetime.datetime.strptime(until_date, "%Y-%m-%d"):
                        continue
                    news_href = news.a.get('href')
                    news_title = news.a.text
                    news_type = news_href.split('/')[4]
                    news_content = self.get_news_content(news_href)
                    # nlp_tag = mynlp.content_nlp(news_content)
                    logger.debug(
                        f'News Title: {news_title} News Type: {news_type} \n'
                        f'News URL: {news_href} News Date Time: {date_time} \n'
                        f'News Content: {news_content}')
                    # ln = LTNNews(
                    #     url=news_href,
                    #     news_type=news_type,
                    #     title=news_title,
                    #     text=news_content,
                    #     created_time=datetime.datetime.strptime(
                    #         date_time, '%Y-%m-%d %H:%M'),
                    #     nlp_tag=nlp_tag,
                    #     pushed=-1,
                    # )
                    # ln.save()
                page += 1
            until_date, middle_date, page = middle_date, since_date, 1
        logger.info(f'Finished get {self.__class__.__name__} Search News.')


class Money(News):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://money.udn.com/money/index'
        self.newest_news_url = 'https://money.udn.com/money/breaknews/1001/0/{page}'
        self.search_url = 'https://money.udn.com/search/result/1001/{search_name}/{page}'

    def get_money_news(self):
        logger.info(f'Starting get {self.__class__.__name__} Newest News.')
        for page in range(1, 5):
            the_newest_news_soup = self.get_soup_from_requests(
                self.newest_news_url.format(page=page))
            news_list = the_newest_news_soup.find(
                'div', class_="area_body").find_all('tr')
            for news in news_list[1:]:
                news_href = news.a.get('href')
                # if MoneyNews.objects.filter(url=news_href):
                #     continue
                news_title = news.a.text
                news_type = news.find('td', align="center").text
                date_time = news.find(
                    'td', align="right", class_="only_web").text
                news_content = self.get_news_content(news_href)
                # nlp_tag = mynlp.content_nlp(news_content)
                logger.debug(
                    f'News Title: {news_title} News Type: {news_type} \n'
                    f'News URL: {news_href} News Date Time: {datetime.datetime.now().year}/{date_time} \n'
                    f'News Content: {news_content}')
                # keyword count
                # keyword_count = self.get_keyword_count(news_content)
                # mn = MoneyNews(
                #     url=news_href,
                #     news_type=news_type,
                #     title=news_title,
                #     text=news_content,
                #     created_time=datetime.datetime.strptime(
                #         f'{datetime.datetime.now().year}/{date_time}', '%Y/%m/%d %H:%M'),
                #     nlp_tag=nlp_tag,
                #     pushed=0,
                #     keyword_count=keyword_count,
                # )
                # mn.save()
                # newsbot.message2bot_by_news(
                #     'Money', news_href)
        logger.info(f'Finished get {self.__class__.__name__} Newest News.')

    def get_news_content(self, url):
        content_soup = self.get_soup_from_requests(url)
        try:
            content_elem = content_soup.find(
                'div', id="article_body").find_all('p')
            content = ''.join([c.text for c in content_elem])
        except:
            content = ''
            logger.exception(f'Get Money {url} Content Fail.')
        try:
            content_created_time = content_soup.find(
                'div', class_="shareBar__info--author").span.text
        except:
            content_created_time = ''
            logger.exception(f'Get Money {url} Content Created Time Fail.')
        try:
            content_type = content_soup.title.text.split(' | ')[2]
        except:
            content_type = ''
            logger.exception(f'Get Money {url} Content Type Time Fail.')

        return content, content_created_time, content_type

    def get_news_by_search(self, search_name, since_date='2020-01-01', until_date='2022-12-31'):
        logger.info(f'Starting get {self.__class__.__name__} Search News.')
        search_soup = self.get_soup_from_requests(
            self.search_url.format(search_name=quote(search_name), page=1))
        news_count = re.search(
            r'\d+', search_soup.find('div', class_="search_info").text).group()
        page = 1
        while page <= math.ceil(int(news_count) / 20):
            search_soup = self.get_soup_from_requests(
                self.search_url.format(search_name=quote(search_name), page=page))
            news_list = search_soup.find(
                'div', id="search_content").find_all('dt')
            for news in news_list:
                date_time = news.span.text.split('：')[1]  # '2020/06/29'
                judge_time = datetime.datetime.strptime(date_time, "%Y/%m/%d")
                if judge_time < datetime.datetime.strptime(since_date, "%Y-%m-%d"):
                    return
                elif judge_time > datetime.datetime.strptime(until_date, "%Y-%m-%d"):
                    continue
                news_href = news.a.get("href")
                news_title = news.h3.text
                news_content, date_time, news_type = self.get_news_content(news_href)  # 2020-06-29 15:50
                # nlp_tag = mynlp.content_nlp(news_content)
                logger.debug(
                    f'News Title: {news_title} News Type: {news_type} \n'
                    f'News URL: {news_href} News Date Time: {date_time} \n'
                    f'News Content: {news_content}')
                # mn = MoneyNews(
                #     url=news_href,
                #     news_type=news_type,
                #     title=news_title,
                #     text=news_content,
                #     created_time=datetime.datetime.strptime(
                #         date_time, '%Y-%m-%d %H:%M'),
                #     nlp_tag=nlp_tag,
                #     pushed=-1,
                # )
                # mn.save()
            page += 1
        logger.info(f'Finished get {self.__class__.__name__} Search News.')


def get_news(news_source_name):
    logger.info(f'Starting get {news_source_name} news.')
    if news_source_name == 'ettoday':
        ettoday = EtToday()
        ettoday.get_ettoday_news()
    elif news_source_name == 'appledaily':
        appledaily = AppleDaily()
        appledaily.get_apple_daily_news()
    elif news_source_name == 'yahoo':
        yahoo = Yahoo()
        yahoo.get_yahoo_news()
    elif news_source_name == 'ebc':
        ebc = EBC()
        ebc.get_ebc_news()
    elif news_source_name == 'tvbs':
        tvbs = TVBS()
        tvbs.get_tvbs_news()
    elif news_source_name == 'setn':
        setn = SETN()
        setn.get_setn_news()
    elif news_source_name == 'ltn':
        ltn = LTN()
        ltn.get_ltn_news()
    elif news_source_name == 'money':
        money = Money()
        money.get_money_news()
    else:
        logger.warning(
            f"Does not have the '{news_source_name}' news source yet.")
        return
    logger.info(f'Finished get {news_source_name} news.')


def get_news_by_search(request):
    news_dict = {'EtToday': EtToday, 'AppleDaily': AppleDaily, 'Yahoo': Yahoo,
                 'TVBS': TVBS, 'EBC': EBC, 'SETN': SETN, 'LTN': LTN, 'Money': Money}
    search_name = request.GET['search_name']
    since_date = request.GET['since_date']
    until_date = request.GET['until_date']
    news_list = request.GET.getlist('news[]')
    for news_source in news_list:
        news_dict[news_source]().get_news_by_search(
            search_name=search_name, since_date=since_date, until_date=until_date)

    # return HttpResponseRedirect('/')


def search_news():
    ettoday = EtToday()
    ettoday.get_news_by_search('蘋果')

    # appledaily = AppleDaily()
    # appledaily.get_news_by_search('愛爾麗')

    # yahoo = Yahoo()
    # yahoo.get_news_by_search('愛爾麗')

    # ebc = EBC()
    # ebc.get_news_by_search('愛爾麗')

    # tvbs = TVBS()
    # tvbs.get_news_by_search('愛爾麗')

    # setn = SETN()
    # setn.get_news_by_search('愛爾麗')

    # ltn = LTN()
    # ltn.get_news_by_search('三倍券')

    # money = Money()
    # money.get_news_by_search('愛爾麗')


if __name__ == '__main__':
    get_news('money')
