import datetime
import logging
import configparser
from urllib.parse import quote
import re
import time
from logging.config import fileConfig
from bs4 import BeautifulSoup

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from fbscrapematerial import rundriver, login_fb_with_cookie, convert_datetime, FBGroupPost, FBFanpagePost

fileConfig('config.ini')
logger = logging.getLogger('FaceBook_Search_Log:')


class FbSearch:
    def __init__(self):
        self.base_url = 'https://www.facebook.com'
        self.search_url = 'https://www.facebook.com/search/posts/?q={search_name}&epa=SERP_TAB'
        self.hashtag_search_url = 'https://www.facebook.com/hashtag/{quote(search_name)}/'
        self.driver = rundriver()
        config = configparser.RawConfigParser()
        config.read('config.ini')
        cookie = config['ACOOKIES']['COOKIE']
        self.login_status = login_fb_with_cookie(self.driver, cookie=cookie)
        self.wait = WebDriverWait(self.driver, 10, 0.5)
        self.save_url = 'https://www.facebook.com/saved'
        self.mobile_hashtag_search_url = 'https://m.facebook.com/hashtag/{search_name}/'

    def get_search_info(self, search_name):
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
                self.get_post_id_info(post_id)
                # user_name = post.find('a', class_="_7gyi").text
                # hovercard = post.find('a', class_="_7gyi").get('data-hovercard')
                # user_id = re.search(r'id=\d+', hovercard).group()[3:]
                # created_time = post.find('span', class_="_6-cm").text  # '7月20日\xa0·\xa0\xa0·\xa0'
                # post_content = post.find('div', class_="_6-cp").text.strip(created_time)
                # comment_count = re.search(r'\d+', post.find('a', class_="_3hg- _42ft").text).group()
                # try:
                #     share_count = re.search(r'\d+', post.find('a', class_="_3rwx _42ft").text).group()
                # except:
                #     share_count = 0
                # like_count = post.find('span', class_="_81hb").text

                # if soup.find('div', class_="phm _64f").text == '無其他結果':  # '無其他結果'
                #     break
        else:
            logger.info('Login Fail.')

    def get_mobile_hashtag_search_post_id(self, search_name):
        if self.login_status:
            self.driver.get(self.mobile_hashtag_search_url.format(search_name=quote(search_name[1:])))
            self.expand_post()  # 展開貼文
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            first_list = soup.find_all('div', class_="_a5o _9_7 _2rgt _1j-f")
            second_list = soup.find('div', {'data-store-id': True}).find_all('div', class_="_55wo _56bf _58k5")
            third_list = soup.find_all('div', {'data-module-role': "PUBLIC_POSTS"})
            post_id_list = []
            for elem in first_list + second_list + third_list:
                try:
                    post_href = elem.find('a', class_="_26yo").get('href')
                except AttributeError:
                    try:
                        post_href = elem.find('a', {'data-sigil': 'feed-ufi-trigger'}).get('href')
                    except:
                        logger.exception(f'Get Mobile hashtag search {search_name} post href fail.')
                        continue
                post_id_list.append(re.search(r'id=\d+', post_href).group()[3:])
            for post in post_id_list:
                self.get_post_id_info(post)
        else:
            logger.info('Login Fail.')

    def get_hashtag_search_info(self):
        if self.login_status:
            self.driver.get(self.hashtag_search_url)
            # 展開貼文
            self.expand_post()
            # 展開'更多'
            see_more_links = self.driver.find_elements_by_xpath(
                "//div[@class='oajrlxb2 g5ia77u1 qu0x051f esr5mh6w e9989ue4 r7d6kgcz rq0escxv nhd2j8a9 nc684nl6 p7hjln8o kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x jb3vyjys rz4wbd8a qt6c0cv9 a8nywdso i1ao9s8h esuyzwwr f1sip0of lzcic4wl oo9gr5id gpro0wi8 lrazzd5p']")
            for comment_message_more_button in see_more_links:
                try:
                    self.driver.execute_script(
                        "arguments[0].click();", comment_message_more_button)
                except Exception:
                    pass
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            self.driver.find_element_by_xpath("//div[@aria-haspopup='menu']").click()  # click ...
            self.driver.find_element_by_css_selector(
                ".oajrlxb2:nth-child(1) > .bp9cbjyn .qzhwtbm6:nth-child(2) > .oi732d6d").click()  # save post
            posts_elem = soup.find('div',
                                   class_="rq0escxv l9j0dhe7 du4w35lb fhuww2h9 gile2uim buofh1pr g5gj957u hpfvmrgz aov4n071 oi9244e8 bi6gxh9e h676nmdw aghb5jc5").find_all(
                'div', class_="du4w35lb k4urcfbm l9j0dhe7 sjgh65i0")
            for post in posts_elem:
                user_name = post.find('strong').text
                post_created_time = post.find('b').text.strip('=')

    def get_post_id_info(self, post_id):
        def get_user_id(element):
            try:
                user_href = element.find('div', class_="nc684nl6").a['href']
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
                    user_id = re.search(r'user/\d+', user_href).group()[5:]
            return user_id

        def get_user_name(element):
            try:
                name = element.find('a', class_="oajrlxb2 g5ia77u1 qu0x051f esr5mh6w e9989ue4 r7d6kgcz rq0escxv nhd2j8a9 nc684nl6 p7hjln8o kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x jb3vyjys rz4wbd8a qt6c0cv9 a8nywdso i1ao9s8h esuyzwwr f1sip0of lzcic4wl oo9gr5id gpro0wi8 lrazzd5p").text
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
            created_time = element.find('div',
                                        class_="oajrlxb2 g5ia77u1 qu0x051f esr5mh6w e9989ue4 r7d6kgcz rq0escxv nhd2j8a9 nc684nl6 p7hjln8o kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x jb3vyjys rz4wbd8a qt6c0cv9 a8nywdso i1ao9s8h esuyzwwr f1sip0of lzcic4wl gmql0nx0 gpro0wi8 b1v8xokw")[
                'aria-label']
            created_time = convert_datetime(created_time)
            return created_time

        def get_message(element):
            try:
                message = element.find('div', class_="ecm0bbzt hv4rvrfc ihqw7lf3 dati1w0a").text
            except AttributeError:
                message = element.find('div', class_="kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x c1et5uql ii04i59q").text
            except:
                message = ''
            return message

        def get_share_count(element):
            try:
                get_shares = element.find('a', text=re.compile(u'次分享')
                                       ).text[:-3].replace(',', '')
            except AttributeError:
                get_shares = 0
            return get_shares

        def get_comment_count(element):
            try:
                comment_count = element.find('span',
                                             class_="d2edcug0 hpfvmrgz qv66sw1b c1et5uql oi732d6d ik7dh3pa fgxwclzu a8c37x1j keod5gw0 nxhoafnm aigsh9s9 d9wwppkn fe6kdd0r mau55g9w c8b282yb iv3no6db jq4qci2q a3bd9o3v knj5qynh m9osqain").text
                comment_count = re.compile(r'(\d+)').findall(comment_count)[0]
            except:
                comment_count = 0
            return comment_count

        self.driver.get(f'{self.base_url}/{post_id}')
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        if re.search(r'posts', self.driver.current_url):
            article = soup.find('div', role="feed")
            # FBFanpagePost(post_id, article=article)
        else:
            article = soup.find('div', attrs={'role': 'article'})
            # FBGroupPost(post_id, article=article)
        try:
            created_time = get_created_time(article)
            user_id = get_user_id(article)
            user_name = get_user_name(article)
            message = get_message(article)
            comment_count = get_comment_count(article)
            share_count = get_share_count(article)
            # Get reactions count
            # reaction_counts = get_post_reactions(self.driver, post_id)
            logger.debug(
                f'Post id: {post_id}, User id: {user_id}, User name: {user_name} \n '
                f'Content: {message} \n '
                f'Created Time: {created_time}, Comment Count: {comment_count}, Share Count: {share_count}')
            if int(comment_count) > 0:
                self.get_post_comment_info(soup, post_id)
        except:
            logger.exception(f'Error when get post: {post_id} info')
            pass

    def get_post_comment_info(self, soup, post_id):
        def get_comment_id(element):
            href = element.find('a', href=re.compile(r'comment_id=\d+'))['href']
            comment_id = re.compile(r'comment_id=(\d+)').findall(href)[0]
            return comment_id

        def get_message(element):
            try:
                message = element.find('span', class_="d2edcug0 hpfvmrgz qv66sw1b c1et5uql oi732d6d ik7dh3pa fgxwclzu a8c37x1j keod5gw0 nxhoafnm aigsh9s9 d9wwppkn fe6kdd0r mau55g9w c8b282yb iv3no6db jq4qci2q a3bd9o3v knj5qynh oo9gr5id").text
            except:
                message = ''
            return message

        def get_user_name(element):
            name = element.find('a', text=True).text
            return name

        def get_uid(element):
            user_href = element.find('a', class_="oajrlxb2 g5ia77u1 qu0x051f esr5mh6w e9989ue4 r7d6kgcz rq0escxv nhd2j8a9 nc684nl6 p7hjln8o kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x jb3vyjys rz4wbd8a qt6c0cv9 a8nywdso i1ao9s8h esuyzwwr f1sip0of lzcic4wl gmql0nx0 gpro0wi8")['href']
            try:
                uid = user_href.split('/')[4]
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
            created_time = element.find('span', class_="tojvnm2t a6sixzi8 abs2jz4q a8s20v7p t1p8iaqh k5wvi7nf q3lfd5jv pk4s997a bipmatt0 cebpdrjk qowsmv63 owwhemhu dp1hu0rb dhp61c6y iyyx5f41").text
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
        comment_element = soup.find('div', class_='cwj9ozl2 tvmbv18p').find_all('ul')
        for elem in comment_element[:-1]:
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


if __name__ == '__main__':
    search_name = '#benq'
    search = FbSearch()
    if re.search(r'#', search_name):
        search.get_mobile_hashtag_search_post_id(search_name)
    else:
        search.get_search_info(search_name)
