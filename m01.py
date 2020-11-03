from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
import requests
import datetime
import re
from bs4 import BeautifulSoup
from logging.config import fileConfig
import logging

fileConfig('config.ini')
logger = logging.getLogger('Mobile01_By_Search_Log:')


class Mobile01:
    def __init__(self, board_cname, q_board='', c_board='', s_board='', f_board='', since_date='2018-01-01',
                 until_date='2022-12-31'):
        self.board_cname = board_cname
        self.q_board, self.c_board, self.s_board, self.f_board = q_board, c_board, s_board, f_board
        self.since_date = datetime.datetime.strptime(since_date, '%Y-%m-%d')
        self.until_date = datetime.datetime.strptime(until_date, '%Y-%m-%d')
        self.base_url = 'https://www.mobile01.com/'
        self.topic_list_url = f'https://www.mobile01.com/topiclist.php?f={f_board}&sort=topictime&p='
        self.forum_topic_url = f'https://www.mobile01.com/forumtopic.php?c={c_board}&s={s_board}&sort=topictime&p='
        self.search_url = f'https://www.mobile01.com/googlesearch.php?q={q_board}&c={c_board}&s={s_board}&f={f_board}'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36'}
        self.driver = self.get_driver_from_firefox()
        self.wait = WebDriverWait(self.driver, 10, 0.5)
        self.driver.implicitly_wait(15)  # 隱性等待

    def get_article_by_board(self):
        for page in range(1, 21):
            if self.f_board:
                board_soup = self.get_soup(f'{self.topic_list_url}{page}')
            else:
                board_soup = self.get_soup(f'{self.forum_topic_url}{page}')
            article_list = board_soup.find('div', class_="l-listTable__tbody").find_all('div', class_="l-listTable__tr")
            for a in article_list:
                article_title = a.find('div', class_="c-listTableTd__title").a.text
                article_href = a.find('div', class_="c-listTableTd__title").a["href"]  # 'topicdetail.php?f=606&t=6184121'
                article_author = a.find_all('div', class_="l-listTable__td l-listTable__td--time")[0].a.text
                article_created_time = a.find_all('div', class_="l-listTable__td l-listTable__td--time")[0].find('div', class_="o-fNotes").text  # '2020-09-06 22:54'
                last_reply_user_name = a.find_all('div', class_="l-listTable__td l-listTable__td--time")[1].a.text
                last_reply_time = a.find_all('div', class_="l-listTable__td l-listTable__td--time")[1].find('div', class_="o-fNotes").text  # '2020-09-07 1:06'
                reply_count = a.find('div', class_="l-listTable__td l-listTable__td--count").find('div', class_="o-fMini").text

    def get_content_and_replies_from_article_url(self, url):
        content_soup = self.get_soup(url)
        page_counts = len(content_soup.find_all('ul', class_="l-pagination"))
        page_counts = 1 if page_counts < 2 else page_counts
        page = 1
        c = content_soup.find_all('div', class_="l-articlePage")[0]
        content_author = c.find('div', class_="l-articlePage__author").find('div', class_="c-authorInfo__id").text.strip()
        content_title = c.find('div', class_="l-docking").find('div', class_="l-docking__title").text.strip()
        content_created_time = c.find('div', class_="l-docking").find('div', class_="l-docking__navigation").find('ul', class_="l-toolBar").find_all('li', class_="l-toolBar__item")[0].text.strip()
        content_view = c.find('div', class_="l-docking").find('div', class_="l-docking__navigation").find('ul', class_="l-toolBar").find_all('li', class_="l-toolBar__item")[1].text.strip()
        content = c.find('div', class_="l-publish__content").find('div', itemprop="articleBody").text.strip()

        while True:
            reply_list = content_soup.find_all('div', class_="l-articlePage")
            for r in reply_list[1:]:
                reply_author = r.find('div', class_="l-articlePage__author").find('div', class_="c-authorInfo__id").text.strip()
                reply_content = r.find('div', class_="l-articlePage__publish").find('article', class_="u-gapBottom--max c-articleLimit").text.strip()
                reply_time = r.find('div', class_="l-articlePage__publish").find('div', class_="l-navigation").span.text  # '2020-09-06 22:58'
            if page <= page_counts:
                page += 1
                content_soup = self.get_soup(f'{url}&p={page}')
            else:
                break

    def get_article_by_search(self):  # by search
        logger.info(f'Starting scan on Mobile01 from search {self.q_board}')
        driver, wait = self.driver, self.wait
        driver.get(self.search_url)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".gsc-selected-option"))).click()
        wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, ".gsc-option-menu-item:nth-child(2) > .gsc-option"))).click()
        page = 1
        while True:
            soup = BeautifulSoup(driver.page_source, 'lxml')
            articles = soup.find_all('div', class_="gsc-webResult gsc-result")
            for a in articles:
                title = a.find('a', class_="gs-title").text
                article_url = a.find('div', class_="gs-bidi-start-align gs-visibleUrl gs-visibleUrl-long").text
                if not self.get_content_from_article_url(title, article_url):
                    continue
                logger.debug(
                    f'Search From: {self.q_board} \n The Page: {page} \n The Title: {title} \n The URL: {article_url}')
            driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
            page += 1
            if page == 11:
                break
            driver.find_element(By.CSS_SELECTOR, f".gsc-cursor-page:nth-child({page})").click()  # next page
        logger.info(f'Finished scan on Mobile01 from search {self.q_board}')

    def get_content_from_article_url(self, title, url):  # by search
        logger.info(f'Starting scan on content from {url}')
        content_soup = self.get_soup(url)
        page_counts = len(content_soup.find_all('ul', class_="l-pagination"))
        try:
            article_author = re.search(r'content=".+" ',
                                       str(content_soup.find('meta', property="dable:author"))).group().strip('" ')[9:]
        except:
            logger.exception(f'{url} get author fail.')
            return False
        try:
            article_context = re.sub(r'\n\s+', '', content_soup.find('div', itemprop="articleBody").text)
        except AttributeError:
            article_context = ''
        except:
            logger.exception(f'Sth error in article context')
        try:
            time_and_views = content_soup.find('div', class_="l-navigation__item is-dockingHide").find_all('li',
                                                                                                           class_="l-toolBar__item")
        except:
            logger.exception(f'{url} get time and view fail')
            pass
        created_time = datetime.datetime.strptime(time_and_views[0].text.replace(
            '\n', ''), '%Y-%m-%d %H:%M')  # '2013-05-05 14:24' %Y=%m-%d %H:%M
        views = time_and_views[1].text.replace('\n', '')
        logger.debug(
            f'author: {article_author} content: {article_context} \n created Time: {created_time} \n Views: {views}')
        self.get_replies_from_page_url(title, url, page_counts, views)
        logger.info(f'Finished scan on content from {url}')

    def get_replies_from_page_url(self, title, url, page_counts, views):  # by search
        logger.info(f'Starting scan on replies from {url}')
        page_counts = 1 if page_counts < 2 else page_counts
        if re.search(r'p=\d+', url) is None:
            page = 1
        else:
            page = int(re.search(r'p=\d+', url).group()[2:])
            url = url[:-4]
        while page <= page_counts:
            replies_soup = self.get_soup(f'{url}&p={page}')
            replies = replies_soup.find_all('div', class_="l-articlePage__publish")
            for reply in replies:
                try:
                    reply_user_id = re.search(r'article_\d+', str(reply)).group().split('_')[1]
                except AttributeError:
                    continue
                reply_content = re.sub(r'\n+\s+', '', reply.find('article').text)
                try:
                    reply_time = datetime.datetime.strptime(
                        reply.find('div', class_="l-navigation__item").text.split('\n')[3], '%Y-%m-%d %H:%M')
                except ValueError:
                    reply_time = datetime.datetime.strptime(
                        reply.find('div', class_="l-navigation__item").text.replace('\n', '').split('#')[0],
                        '%Y-%m-%d %H:%M')
                logger.debug(f'{reply_user_id} \n {reply_content} \n {reply_time}')
                # if self.since_date < reply_time < self.until_date:

            page += 1
        logger.info(f'Finished scan on replies from {url}')

    def get_driver_from_firefox(self):
        options = Options()
        options.headless = True
        return webdriver.Firefox(options=options)

    def get_soup(self, url):
        try:
            response = requests.get(url=url, headers=self.headers)
        except:
            logger.exception(f'Get URL: {url} requests fail.')

        return BeautifulSoup(response.text, 'lxml')


def main():
    # since_date, until_date, board_cname = request.GET['since_date'], request.GET['until_date'], request.GET[
    #     'board_cname']
    # q_board, c_board, s_board, f_board = request.GET['q_board'], request.GET['c_board'], request.GET['s_board'], \
    #                                      request.GET['f_board']

    search_form = Mobile01(board_cname='', q_board='', c_board='26', s_board='1', f_board='',)
    search_form.get_article_by_board()
    search_form.driver.quit()
    # return HttpResponseRedirect


if __name__ == '__main__':
    main()
