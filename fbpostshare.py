import re
import configparser
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import datetime
from bs4 import BeautifulSoup
from fbscrapematerial import rundriver, convert_datetime, login_fb_with_cookie
from logging.config import fileConfig
import logging

fileConfig('config.ini')
logger = logging.getLogger('GetShareInfo_Log:')


def get_share_info(post_source, source_id, post_id):
    """
    :param post_source: PostLists or GroupPost
    :param source_id: fanpage_id or group_id
    """
    logger.info(f'Starting get post {post_id} share info.')
    s_driver = rundriver()
    config = configparser.RawConfigParser()
    config.read('config.ini')
    cookie = config['ACOOKIES']['COOKIE']
    login = login_fb_with_cookie(s_driver, cookie)
    if login:
        url = 'https://www.facebook.com/' + post_id
        s_driver.get(url)
        time.sleep(4)
        # close 彈跳頁面
        try:
            WebDriverWait(s_driver, 5, 0.5).until(ec.visibility_of_element_located(
                (By.XPATH, ("//a[@class='_xlt _418x']")))).click()
        except:
            logger.info('No alert.')
            pass
        # get the post share count
        post_soup = BeautifulSoup(s_driver.page_source, 'lxml')
        shares_count = post_soup.find_all('span',
                                          class_="d2edcug0 hpfvmrgz qv66sw1b c1et5uql oi732d6d ik7dh3pa fgxwclzu a8c37x1j keod5gw0 nxhoafnm aigsh9s9 d9wwppkn fe6kdd0r mau55g9w c8b282yb iv3no6db jq4qci2q a3bd9o3v knj5qynh m9osqain")[
            1].text
        shares_count = post_soup.find_all('span',
                                          class_="d2edcug0 hpfvmrgz qv66sw1b c1et5uql oi732d6d ik7dh3pa fgxwclzu a8c37x1j keod5gw0 nxhoafnm aigsh9s9 d9wwppkn fe6kdd0r mau55g9w c8b282yb iv3no6db jq4qci2q a3bd9o3v knj5qynh m9osqain")[
            1].text
        shares_count = shares_count[:-3].strip(',')
        try:  # click share alert
            s_driver.find_elements_by_xpath(
                "//span[@class='d2edcug0 hpfvmrgz qv66sw1b c1et5uql oi732d6d ik7dh3pa fgxwclzu a8c37x1j keod5gw0 nxhoafnm aigsh9s9 d9wwppkn fe6kdd0r mau55g9w c8b282yb iv3no6db jq4qci2q a3bd9o3v knj5qynh m9osqain']")[
                1].click()
        except:
            logger.exception('Click Share alert Fail.')
        # wait share alert pop
        WebDriverWait(s_driver, 5, 0.5).until(
            ec.visibility_of_element_located((By.XPATH, "//div[@aria-label='轉貼這個連結的人']")))
        s_driver.maximize_window()
        # expand share alert
        target = s_driver.find_element_by_xpath(
            "//span[@class='d2edcug0 hpfvmrgz qv66sw1b c1et5uql oi732d6d ik7dh3pa fgxwclzu a8c37x1j keod5gw0 nxhoafnm aigsh9s9 d9wwppkn fe6kdd0r mau55g9w c8b282yb mdeji52x e9vueds3 j5wam9gi lrazzd5p m9osqain hzawbc8m']")
        start_time = time.time()
        while True:
            try:
                target.location_once_scrolled_into_view
                time.sleep(1)
                if len(s_driver.find_elements_by_xpath("//div[@aria-label='轉貼這個連結的人']//div[@class='sjgh65i0']")) == int(shares_count):
                    break
                else:  # 往上拉
                    locate_elem = s_driver.find_elements_by_xpath("//div[@aria-label='轉貼這個連結的人']//div[@class='sjgh65i0']")[0]
                    locate_elem.location_once_scrolled_into_view
                    time.sleep(1)
                if time.time() - start_time > 60:
                    break
            except:
                logger.exception('Something error in expand share alert.')
                pass

        soup = BeautifulSoup(s_driver.page_source, 'lxml')
        share_dialog_lst = soup.find('div', {'aria-label': '轉貼這個連結的人'}).find_all('div', class_="sjgh65i0")
        for share in share_dialog_lst[:-2]:
            try:
                user_name = share.find('a',
                                       class_="oajrlxb2 g5ia77u1 qu0x051f esr5mh6w e9989ue4 r7d6kgcz rq0escxv nhd2j8a9 nc684nl6 p7hjln8o kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x jb3vyjys rz4wbd8a qt6c0cv9 a8nywdso i1ao9s8h esuyzwwr f1sip0of lzcic4wl oo9gr5id gpro0wi8 lrazzd5p").text
            except AttributeError:  # not a share div
                continue
            try:
                share_content = share.find('div', class_="kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x c1et5uql ii04i59q").text
            except AttributeError:  # 顯示附件
                share_content = share.find('span',
                                           class_="a8c37x1j ni8dbmo4 stjgntxs l9j0dhe7 ltmttdrg g0qnabr5").text
                pass
            share_href = share.find('a',
                                    class_="oajrlxb2 g5ia77u1 qu0x051f esr5mh6w e9989ue4 r7d6kgcz rq0escxv nhd2j8a9 nc684nl6 p7hjln8o kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x jb3vyjys rz4wbd8a qt6c0cv9 a8nywdso i1ao9s8h esuyzwwr f1sip0of lzcic4wl oo9gr5id gpro0wi8")[
                "href"]
            user_id = share_href.split('/')[3].split('?')[0]
            share_created_time = share.find('b', class_="b6zbclly myohyog2 l9j0dhe7 aenfhxwr l94mrbxd ihxqhq3m nc684nl6 t5a262vz sdhka5h4").text
            created_time = convert_datetime(share_created_time.strip('='))
            logger.debug(f"Share's user name: {user_name} User ID: {user_id} \n"
                         f"Share Content: {share_content} \n"
                         f"Share created time: {created_time}")
    else:
        logger.warning('Login Fail.')
    s_driver.quit()
    logger.info(f'Finished get post {post_id} share info.')


if __name__ == '__main__':
    post_source = 'PostLists'
    source_id = 'swayhouse'
    post_id = '3150265658341907'
    get_share_info(post_source, source_id, post_id)
