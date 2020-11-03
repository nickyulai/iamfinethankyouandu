from datetime import datetime, timedelta
import time
import re
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from logging.config import fileConfig
import logging

fileConfig('config.ini')
logger = logging.getLogger('FBScrapeMaterial_Log:')


# get driver
def rundriver():
    options = Options()
    # options.add_argument('--headless')
    # options.add_argument('--no-sandbox')
    options.add_argument('blink-settings=imagesEnabled=false')
    # options.add_argument('--disable-dev-shm-usage')
    drievr = webdriver.Chrome(chrome_options=options)
    return drievr


# add cookie to selenium to login fb
def login_fb_with_cookie(driver, cookie):
    try:
        cookie_data = cookie.split('; ')
        driver.get('https://www.facebook.com')
        for item in cookie_data:
            item = item.split('=')
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
                ec.presence_of_element_located((By.XPATH, '//*[text()="首頁"]')))
            login_status = True
        except:
            login_status = False
    except Exception:
        logger.exception('Add Cookie Error.')
        login_status = False
    finally:
        return login_status


# convert fb date type to datetime type
def convert_datetime(date_time):
    if '剛剛' in date_time:
        date_time = datetime.now()
        return date_time
    if '分鐘' in date_time:
        date_time = datetime.now() - timedelta(minutes=int(re.search(r'\d+', date_time).group()))
        return date_time
    if '小時' in date_time:
        date_time = datetime.now() - timedelta(hours=int(re.search(r'\d+', date_time).group()))
        return date_time
    if '天' in date_time:
        date_time = datetime.now() - timedelta(days=int(re.search(r'\d+', date_time).group()))
        return date_time
    if '週' in date_time:
        date_time = datetime.now() - timedelta(days=7*int(re.search(r'\d+', date_time).group()))
        return date_time
    if '年' in date_time:
        date_time = datetime.strptime(date_time, '%Y年%m月%d日')
        return date_time
    if '昨天' in date_time:
        d_time = datetime.now() - timedelta(days=1)
    else:
        d_time = re.compile(r'\d+月\d+日').findall(date_time)[0]
        d_time = datetime.strptime(f'{datetime.now().year}年{d_time}', '%Y年%m月%d日')
    if '上午' in date_time:
        c_time = re.compile(r'(上午\d+:\d+)').findall(date_time)[0]
        c_time = datetime.strptime(c_time, '上午%I:%M')
    elif '下午' in date_time:
        c_time = re.compile(r'(下午\d+:\d+)').findall(date_time)[0]
        c_time = datetime.strptime(c_time, '下午%I:%M') + timedelta(hours=12)
    else:
        return d_time
    date_time = datetime.combine(d_time.date(), c_time.time())
    return date_time


# get each post reaction count with selenium
def get_post_reactions_with_selenium(driver, post_id):
    reactions = {'like': '讚', 'love': '大心', 'wow': '哇',
                 'haha': '哈', 'sad': '嗚', 'angry': '怒', 'care': '加油'}
    logger.info('Start get reactions: ' + post_id)
    url = 'https://m.facebook.com/ufi/reaction/profile/browser/?ft_ent_identifier={}'.format(
        post_id)
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    area_column = soup.find('div', class_="scrollAreaColumn")
    reaction_counts = {}
    for reaction_type in reactions:
        reaction = reactions[reaction_type]
        try:
            counts = area_column.find(
                'span', attrs={'aria-label': re.compile(r'{0}'.format(reaction))}).text
            if re.search(u'萬', counts):
                reaction_counts[reaction_type] = int(
                    re.search(r'\d+,*\d+', counts).group().replace(',', '')) * 10000
            else:
                reaction_counts[reaction_type] = int(
                    re.search(r'\d+,*\d+', counts).group().replace(',', ''))
        except:
            reaction_counts[reaction_type] = 0
            pass
    reaction_counts['all_count'] = sum(reaction_counts.values())
    logger.info(reaction_counts)
    return reaction_counts


# get each post reaction count with requests
def get_post_reactions_with_requests(post_id, fb_app, fb_userid):
    session = requests.Session()
    cookie = SocialToken.objects.get(app=fb_app.id, account=fb_userid)
    c = {'Cookie': cookie.token_secret}
    reactions = {'like': '讚', 'love': '大心', 'wow': '哇',
                 'haha': '哈', 'sad': '嗚', 'angry': '怒', 'care': '加油'}
    logger.info(post_id, )
    url = 'https://m.facebook.com/ufi/reaction/profile/browser/?ft_ent_identifier={}'.format(
        post_id)
    response = session.get(url, cookies=c)
    soup = BeautifulSoup(response.text, 'lxml')
    reaction_counts = {}
    for reaction_type in reactions:
        reaction = reactions[reaction_type]
        try:
            href = soup.find('img', alt=reaction).parent['href']
            counts = int(re.compile(r'total_count=(\d+)&').findall(href)[0])
            reaction_counts[reaction_type] = counts
        except:
            reaction_counts[reaction_type] = 0
            pass
    reaction_counts['all_count'] = sum(reaction_counts.values())
    logger.info(reaction_counts, )

    return reaction_counts


def get_fb_post_comments_info(driver, post_id):
    def get_comment_id(element):
        href = element.find('a', href=re.compile(r'comment_id=\d+'))['href']
        comment_id = re.compile(r'comment_id=(\d+)').findall(href)[0]
        return comment_id

    def get_message(element):
        try:
            message = element.find('span',
                                   class_="d2edcug0 hpfvmrgz qv66sw1b c1et5uql oi732d6d ik7dh3pa fgxwclzu a8c37x1j keod5gw0 nxhoafnm aigsh9s9 d9wwppkn fe6kdd0r mau55g9w c8b282yb iv3no6db jq4qci2q a3bd9o3v knj5qynh oo9gr5id").text
        except:
            message = ''
        return message

    def get_user_name(element):
        name = element.find('a', text=True).text
        return name

    def get_uid(element):
        user_href = element.find('a',
                                 class_="oajrlxb2 g5ia77u1 qu0x051f esr5mh6w e9989ue4 r7d6kgcz rq0escxv nhd2j8a9 nc684nl6 p7hjln8o kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x jb3vyjys rz4wbd8a qt6c0cv9 a8nywdso i1ao9s8h esuyzwwr f1sip0of lzcic4wl gmql0nx0 gpro0wi8")[
            'href']
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
        created_time = element.find('span',
                                    class_="tojvnm2t a6sixzi8 abs2jz4q a8s20v7p t1p8iaqh k5wvi7nf q3lfd5jv pk4s997a bipmatt0 cebpdrjk qowsmv63 owwhemhu dp1hu0rb dhp61c6y iyyx5f41").text
        created_time = convert_datetime(created_time)
        return created_time

    start_time = time.time()
    # 留言展開
    while True:
        try:
            WebDriverWait(driver, 10, 0.5).until(
                ec.visibility_of_element_located((By.CLASS_NAME, ("_4ssp")))).click()
            if time.time() - start_time > 60:
                break
        except:
            break
    # '更多' 展開
    try:
        for e in driver.find_elements_by_class_name('_4sso'):
            e.click()
            time.sleep(0.25)
    except:
        pass
    soup = BeautifulSoup(driver.page_source, 'lxml')
    comment_element = soup.find('div', class_='cwj9ozl2 tvmbv18p').find_all('ul')
    for elem in comment_element[-1]:
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


class FBGroupPost:
    def __init__(self, post_id, driver=None, article=None):
        self.base_url = 'https://www.facebook.com'
        self.post_url = 'https://www.facebook.com/{post_id}'
        self.post_id = post_id
        self.driver = driver
        self.article = article
        self.get_post_info()

    def get_post_info(self):
        if self.article:
            article = self.article
        else:
            self.driver.get(self.post_url)
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            article = soup.find('div', attrs={'role': 'article'})
        try:
            created_time = self.get_created_time(article)
            user_id = self.get_user_id(article)
            user_name = self.get_user_name(article)
            message = self.get_message(article)
            comment_count = self.get_comment_count(article)
            share_count = self.get_share_count(article)
            # Get reactions count
            # reaction_counts = get_post_reactions(self.driver, post_id)
            logger.debug(
                f'Post id: {self.post_id}, User id: {user_id}, User name: {user_name} \n '
                f'Content: {message} \n '
                f'Created Time: {created_time}, Comment Count: {comment_count}, Share Count: {share_count}')
            if int(comment_count) > 0:
                get_fb_post_comments_info(self.driver, self.post_id)
        except:
            logger.exception(f'Error when get post: {self.post_id} info')
            pass

    def get_user_id(self, element):
        try:
            user_href = element.find(
                'a', attrs={'data-hovercard': True})['data-hovercard']
        except:
            try:
                user_href = element.find(
                    'a', href=re.compile(r'profile.php?'))['href']
            except:
                user_href = element.find('div', class_="nc684nl6").a['href']
        try:
            user_id = re.compile(r'\?id=([-_%\w\d]+)').findall(user_href)[0]
        except:
            try:
                user_id = re.compile(
                    r'facebook.com/([-_%\w\d\.]+)/').findall(user_href)[0]
            except:
                user_id = re.search(r'user/\d+', user_href).group()[5:]
        return user_id

    def get_user_name(self, element):
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

    def get_created_time(self, element):
        created_time = element.find('div',
                                    class_="oajrlxb2 g5ia77u1 qu0x051f esr5mh6w e9989ue4 r7d6kgcz rq0escxv nhd2j8a9 nc684nl6 p7hjln8o kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x jb3vyjys rz4wbd8a qt6c0cv9 a8nywdso i1ao9s8h esuyzwwr f1sip0of lzcic4wl gmql0nx0 gpro0wi8 b1v8xokw")[
            'aria-label']
        created_time = convert_datetime(created_time)
        return created_time

    def get_message(self, element):
        try:
            message = element.find(
                'div', attrs={'data-testid': 'post_message'}).text
        except:
            message = ''
        return message

    def get_share_count(self, element):
        try:
            get_shares = element.find('a', text=re.compile(u'次分享')
                                      ).text[:-3].replace(',', '')
        except KeyError:
            logger.warning('no body want share!!!')
            get_shares = 0
        except ArithmeticError:
            get_shares = 0
        return get_shares

    def get_comment_count(self, element):
        try:
            comment_count = element.find('a', text=re.compile('則留言')).text
            comment_count = re.compile(r'(\d+)').findall(comment_count)[0]
        except TypeError:
            comment_count = re.search(
                r'\d*,*\d+', element.find('a', class_="_3hg- _42ft").text).group().replace(',', '')
        except:
            comment_count = 0
        return comment_count


class FBFanpagePost:
    def __init__(self, post_id, driver=None, article=None):
        self.base_url = 'https://www.facebook.com'
        self.post_url = 'https://www.facebook.com/{post_id}'
        self.post_id = post_id
        self.driver = driver
        self.article = article

    def get_post_info(self):
        pass
