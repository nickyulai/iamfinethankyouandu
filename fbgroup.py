# import json
import logging
# import random
import re
import time
from datetime import datetime, timedelta
from logging.config import fileConfig
from fbsearch import add_cookie
import pytz
# import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


fileConfig('config.ini')
logger = logging.getLogger('GroupScrap_Log:')


def get_group_post_by_scheduled(fb_userid, group_id):
    try:
        loctz = pytz.timezone('Asia/Taipei')
        driver = rundriver()
        login = add_cookie(driver, group_id)
        since_date = datetime.strptime('2020-07-01', '%Y-%m-%d')
        until_date = since_date + timedelta(hours=1)
        if login:
            get_content(driver, fb_userid, group_id, since_date, until_date)
        else:
            logger.warning('login failed')
    except:
        logger.exception('The program is Fail.')
        pass
    finally:
        driver.quit()


def get_group_post(request):
    try:
        group_id = request.GET['group_id']
        driver = rundriver()
        login = add_cookie(driver, group_id)
        if login:
            since_date = datetime.strptime(
                request.GET['since_date'], '%Y-%m-%d')
            until_date = datetime.strptime(
                request.GET['until_date'], '%Y-%m-%d')
            get_content(driver, fb_user_id, group_id, since_date, until_date)
        else:
            logger.warning('login failed')
    except:
        logger.exception('The program is Fail.')
        pass
    finally:
        driver.quit()
    return HttpResponseRedirect('/')


def get_content(driver, fb_userid, group_id, since_date, until_date):
    def get_user_id(element):
        try:
            user_href = element.find(
                'a', attrs={'data-hovercard': True})['data-hovercard']
        except:
            try:
                user_href = element.find(
                    'a', href=re.compile('profile.php?'))['href']
            except:
                user_href = element.find('a', class_='profileLink')['href']
        try:
            user_id = re.compile(r'\?id=([-_%\w\d]+)').findall(user_href)[0]
        except:
            try:
                user_id = re.compile(
                    r'facebook.com/([-_%\w\d\.]+)/').findall(user_href)[0]
            except:
                user_id = re.compile(
                    r'facebook.com/([-_%\w\d\.]+)\?').findall(user_href)[0]
        return user_id

    def get_user_name(element):
        try:
            name = element.find('a', rel="dialog")['title']
            # name = element.find('a', rel="dialog").next_element
        except:
            name = element.find('a', href=True, attrs={
                'data-hovercard': True})['title']
        return name

    def get_post_id(element):
        post_href = element.find('a', href=re.compile('permalink/'))['href']
        post_id = re.compile(r'permalink/(\d+)/').findall(post_href)[0]
        return post_id

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

    def get_reaction_count(element):
        try:
            reaction_count = int(element.find(
                'a', attrs={'data-testid': 'UFI2ReactionsCount/root'}).find('span').text)
        except:
            reaction_count = 0
        return reaction_count

    def get_comment_count(element):
        try:
            comment_count = element.find('a', text=re.compile('則留言')).text
            comment_count = re.compile(r'(\d+)').findall(comment_count)[0]
        except:
            comment_count = 0
        return comment_count

    def get_all_count(element):
        try:
            all_count = element.find('span', class_="_81hb").text
        except:
            all_count = 0
        return all_count

    url = 'https://www.facebook.com/groups/' + \
          group_id + '/?sorting_setting=CHRONOLOGICAL'
    driver.get(url)
    expand_post(driver, since_date)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    feed = soup.find('div', attrs={'aria-label': '動態消息'})
    article = feed.find_all('div', attrs={'role': 'article'}, recursive=False)
    # get_the_group_post_id_query_set_from_sql = GroupPost.objects.filter(
    #     group_id='{}'.format(group_id)).values('post_id').order_by('-created_time')
    # the_group_post_id_list = []
    # check if postid is in sql
    # if get_the_group_post_id_query_set_from_sql:
    #     for post in get_the_group_post_id_query_set_from_sql:
    #         the_group_post_id_list.append(post['post_id'])
    for a in article:
        try:
            created_time = get_created_time(a)
            if created_time < since_date or created_time > until_date:
                continue
            post_id = get_post_id(a)
            # if post_id in the_group_post_id_list:
            #     continue
            user_id = get_user_id(a)
            user_name = get_user_name(a)
            message = get_message(a)
            reaction_count = get_reaction_count(a)
            comment_count = get_comment_count(a)
            all_count = get_all_count(a)
            # Get reactions count
            reaction_counts = get_post_reactions(driver, post_id)

            logger.info('PostID:{}, CreatedTime:{}, Likes:{}, Comments:{}'.format(
                post_id, created_time, reaction_count, comment_count))

            pushed = -1
            get_comment(driver, group_id, post_id)
        except:
            pass


def get_comment(driver, group_id, post_id):
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

    url = 'https://www.facebook.com/' + post_id
    driver.get(url)
    start_time = time.time()
    # 留言展開
    while True:
        try:
            WebDriverWait(driver, 2, 0.5).until(
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

    soup = BeautifulSoup(driver.page_source, 'html.parser')
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
        except:
            logger.warning('PostID #{} commentID : {} failed!'.format(
                post_id, comment_id), user_name, uid)


def rundriver():
    options = Options()
    options.add_argument('--headless')
    # options.add_argument('--no-sandbox')
    options.add_argument('blink-settings=imagesEnabled=false')
    # options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(chrome_options=options)
    return driver


# def add_cookie(driver):
#     config = configparser.RawConfigParser()
#     config.read('config.ini')
#     c_name = config['GCOOKIES']['NAME']
#     c_value = config['GCOOKIES']['VALUE']
#     c_name = c_name.split(',')
#     c_value = c_value.split(',')
#     login_status = False
#     try:
#         driver.get('https://www.facebook.com', )
#         if login_status is False:
#             for item in zip(c_name, c_value):
#                 driver.add_cookie({
#                     'domain': '.facebook.com',
#                     'name': item[0],
#                     'value': item[1],
#                     'path': '/',
#                     'expires': None
#                 })
#             driver.refresh()
#             time.sleep(2)
#             try:
#                 WebDriverWait(driver, 5, 0.5).until(
#                     EC.presence_of_element_located((By.XPATH, '//*[text()="首頁"]')))
#                 login_status = True
#             except:
#                 login_status = False
#     except Exception:
#         logger.exception('Add Cookie Error.')
#         login_status = False
#     finally:
#         return login_status


# convert FB date type to datetime.datetime
def convert_datetime(date_time):
    date, ctime = date_time.split(' ')
    date = datetime.strptime(date, '%Y年%m月%d日')
    if '上午' in ctime:
        ctime = re.compile(r'(上午\d+:\d+)').findall(ctime)[0]
        ctime = datetime.strptime(ctime, '上午%I:%M')
    elif '下午' in ctime:
        ctime = re.compile(r'(下午\d+:\d+)').findall(ctime)[0]
        ctime = datetime.strptime(ctime, '下午%I:%M') + timedelta(hours=12)
    date_time = datetime.combine(date.date(), ctime.time())
    return date_time


# expand post to since date
def expand_post(driver, since_date):
    def scroll_to_bottom():
        driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")

    while True:
        post_date_elements = driver.find_elements_by_xpath('//abbr[@title]')
        last_date = convert_datetime(
            post_date_elements[-1].get_attribute('title'))
        if last_date < since_date:
            logger.info(f'{last_date} || {since_date}')
            break
        scroll_to_bottom()


# get each post reaction count
def get_post_reactions(driver, post_id):
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

if __name__ == '__main__':
