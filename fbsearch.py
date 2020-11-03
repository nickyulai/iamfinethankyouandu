import logging
import configparser
from urllib.parse import quote
import re
import time
from logging.config import fileConfig
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


fileConfig('config.ini')
logger = logging.getLogger('FaceBook_Search_Log:')


# add cookie to selenium to login fb
def add_cookie(driver):
    config = configparser.RawConfigParser()
    config.read('config.ini')
    c_name = config['COOKIES']['NAME']
    c_value = config['COOKIES']['VALUE']
    c_name = c_name.split(',')
    c_value = c_value.split(',')
    login_status = False
    try:
        driver.get('https://www.facebook.com', )
        if login_status is False:
            for item in zip(c_name, c_value):
                driver.add_cookie({
                    'domain': '.facebook.com',
                    'name': item[0],
                    'value': item[1],
                    'path': '/',
                    'expires': None
                })
            driver.refresh()
            time.sleep(2)
            try:
                WebDriverWait(driver, 5, 0.5).until(
                    EC.presence_of_element_located((By.XPATH, '//*[text()="首頁"]')))
                login_status = True
            except:
                login_status = False
    except Exception:
        logger.exception('Add Cookie Error.')
        login_status = False
    finally:
        return login_status


class FbSearch:
    def __init__(self):
        self.base_url = 'https://www.facebook.com'
        self.search_url = 'https://www.facebook.com/search/posts/?q={search_name}&epa=SERP_TAB'
        self.driver = rundriver()
        self.login_status = add_cookie(self.driver)
        self.wait = WebDriverWait(self.driver, 10, 0.5)
        self.save_url = 'https://www.facebook.com/saved'
        self.mobile_hashtag_search_url = 'https://m.facebook.com/hashtag/{search_name}/'

    def get_search_info(self, search_name):
        logger.info('Starting get search in website.')
        if self.login_status:
            self.driver.get(self.search_url.format(search_name=quote(search_name)))
            self.expand_post()
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            posts_elem = soup.find('div', class_="_401d").find_all('div', class_="_19_p")
            for post in posts_elem:
                post_href = post.find('span', class_="_6-cm").a.get('href')
                try:
                    if re.search(r'groups', post_href):
                        post_id = post_href.split('/')[2]
                    else:
                        post_id = post_href.split('/')[3]
                except:
                    continue
                self.get_post_id_info(post_id, search_name)
            logger.info('Finished get search in website.')
        else:
            logger.warning('Login Fail.')

    def get_mobile_hashtag_search_post_id(self, search_name):
        logger.info('Starting get hashtag search in mobile.')
        if self.login_status:
            self.driver.get(self.mobile_hashtag_search_url.format(search_name=quote(search_name[1:])))
            self.expand_post()  # 展開貼文
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            first_list = soup.find_all('div', class_="_a5o _9_7 _2rgt _1j-f")
            second_list = soup.find('div', {'data-store-id': True}).find_all('div', class_="_55wo _56bf _58k5")
            post_id_list = []
            for elem in first_list + second_list:
                try:
                    post_href = elem.find('a', class_="_26yo").get('href')
                    post_id_list.append(re.search(r'id=\d+', post_href).group()[3:])
                except:
                    logger.exception('Sth error when get post id in mobile hashtag search.')
                    pass
            for post in post_id_list:
                if FbSearchPostInfo.objects.filter(post_id=post):
                    continue
                self.get_post_id_info(post, search_name)
            logger.info('Finished get hashtag search in mobile.')
        else:
            logger.warning('Login Fail.')

    def get_post_id_info(self, post_id, search_name):
        def get_user_id(element):
            try:
                user_href = element.find(
                    'a', attrs={'data-hovercard': True})['data-hovercard']
            except:
                try:
                    user_href = element.find(
                        'a', href=re.compile('profile.php?'))['href']
                except:
                    try:
                        user_href = element.find('a', class_='profileLink')['href']
                    except:
                        user_href = element.a.get('href')
            try:
                user_id = re.compile(r'\?id=([-_%\w\d]+)').findall(user_href)[0]
            except:
                try:
                    user_id = re.compile(
                        r'facebook.com/([-_%\w\d\.]+)/').findall(user_href)[0]
                except:
                    try:
                        user_id = re.compile(
                            r'facebook.com/([-_%\w\d\.]+)\?').findall(user_href)[0]
                    except:
                        user_id = user_href.split('/')[1]
            return user_id

        def get_user_name(element):
            try:
                name = element.find('a', rel="dialog")['title']
                # name = element.find('a', rel="dialog").next_element
            except KeyError:
                try:
                    name = element.find('span', class_="fwb fcg").text
                except:
                    name = element.find('a', class_="profileLink").text
            except:
                name = element.find('a', href=True, attrs={
                    'data-hovercard': True})['title']
            return name

        def get_created_time(element):
            created_time = element.find('abbr')['title']
            created_time = convert_datetime(created_time)
            return created_time

        def get_message(element):
            try:
                message = element.find(
                    'div', attrs={'data-testid': 'post_message'}).text
            except:
                message = ''
            return message

        def get_share_count(element):
            try:
                get_shares = element.find('a', text=re.compile(u'次分享')
                                       ).text[:-3].replace(',', '')
            except KeyError:
                logger.warning('nobody want share!!!')
                get_shares = 0
            except AttributeError:
                get_shares = 0
            return get_shares

        def get_comment_count(element):
            try:
                comment_count = element.find('a', text=re.compile('則留言')).text
                comment_count = re.compile(r'(\d+)').findall(comment_count)[0]
            except TypeError:
                comment_count = re.search(
                    r'\d*,*\d+', element.find('a', class_="_3hg- _42ft").text).group().replace(',', '')
            except:
                comment_count = 0
            return comment_count

        logger.info(f'Starting get Post id: {post_id} info.')
        self.driver.get(f'{self.base_url}/{post_id}')
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        if re.search(r'posts', self.driver.current_url):
            article = soup.find('div', role="feed")
        else:
            article = soup.find('div', attrs={'role': 'article'})
        try:
            created_time = get_created_time(article)
            user_id = get_user_id(article)
            user_name = get_user_name(article)
            message = get_message(article)
            comment_count = get_comment_count(article)
            share_count = get_share_count(article)
            # Get reactions count
            reaction_counts = get_post_reactions(self.driver, post_id)
            logger.debug(
                f'Post id: {post_id}, User id: {user_id}, User name: {user_name} \n '
                f'Content: {message} \n '
                f'Created Time: {created_time}, Comment Count: {comment_count}, Share Count: {share_count}')
            fpi = FbSearchPostInfo(
                search_name=search_name,
                post_id=post_id,
                user_id=user_id,
                user_name=user_name,
                message=message,
                created_time=created_time,
                comment_count=comment_count,
                share_count=share_count,
                like_count=reaction_counts['all_count'],
            )
            fpi.save()
            logger.info(f'Finished get Post id: {post_id} info.')
            if int(comment_count) > 0:
                self.get_post_comment_info(soup, post_id, search_name)
        except:
            logger.exception(f'Error when get post: {post_id} info')
            pass

    def get_post_comment_info(self, soup, post_id, search_name):
        def get_comment_id(element):
            href = element.find('a', href=re.compile(r'comment_id=\d+'))['href']
            comment_id = re.compile(r'comment_id=(\d+)').findall(href)[0]
            return comment_id

        def get_message(element):
            try:
                message = element.find('span', attrs={'dir': 'ltr'}).text
            except:
                message = ''
            return message

        def get_user_name(element):
            name = element.find('a', text=True).text
            return name

        def get_uid(element):
            user_href = element.find('a', text=True)['data-hovercard']
            try:
                uid = re.compile(r'\?id=(\d+)&').findall(user_href)[0]
            except:
                uid = re.compile(r'/([-_%\w\d\.]+)\?').findall(user_href)[0]
            return uid

        def get_reaction_count(element):
            try:
                reaction_count = int(element.find(
                    'a', href=re.compile('reaction')).text)
            except:
                reaction_count = 0
            return reaction_count

        def get_created_time(element):
            created_time = element.find('abbr')['data-tooltip-content']
            created_time = convert_datetime(created_time)
            return created_time

        start_time = time.time()
        # 留言展開
        while True:
            try:
                self.wait.until(
                    EC.visibility_of_element_located((By.CLASS_NAME, ("_4ssp")))).click()
                if time.time() - start_time > 60:
                    break
            except:
                break
        # '更多' 展開
        try:
            for e in self.driver.find_elements_by_class_name('_4sso'):
                e.click()
                time.sleep(0.25)
        except:
            pass
        logger.info(f'Starting get Post: {post_id} comments.')
        comment_element = soup.find('div', class_='userContentWrapper').find_all(
            'div', attrs={'role': 'article'})
        for elem in comment_element:
            try:
                comment_id = get_comment_id(elem)
                user_name = get_user_name(elem)
                uid = get_uid(elem)
                created_time = get_created_time(elem)
                reaction_count = get_reaction_count(elem)
                message = get_message(elem)
                logger.debug(f'Post id: {post_id}, Comment id: {comment_id} \n'
                             f'User name: {user_name}, Uid: {uid} \n'
                             f'Created time: {created_time}, Reaction count: {reaction_count} \n'
                             f'Message: {message}')
                fpci = FbSearchPostCommentInfo(
                    search_name=search_name,
                    post_id=post_id,
                    comment_id=comment_id,
                    user_id=uid,
                    user_name=user_name,
                    message=message,
                    like_count=reaction_count,
                    created_time=created_time,
                )
                fpci.save()
                logger.info(f'Finished get Post: {post_id} comments.')
            except:
                logger.exception(f'Error when get post: {post_id} comments.')
                pass

    # expand post to since date
    def expand_post(self):
        def scroll_to_bottom():
            self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")

        now_time = time.time()
        while True:
            if (time.time() - now_time) > 30:
                break
            scroll_to_bottom()

