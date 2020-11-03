import configparser
import logging
import os
import re
from logging.config import fileConfig

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

fileConfig('config.ini')
logger = logging.getLogger('SkyWalkerLog:')


class FBConvertUserID:
    def __init__(self, uid=None):
        self.fb_base_url = 'https://www.facebook.com/'
        self.look_up_url = 'https://lookup-id.com/#'
        self.uid = uid
        self.fb_user_url = f'{self.fb_base_url}{self.uid}'
        self.driver = self.get_driver()
        self.get_numeric_id_by_lookupid()
        # self.login = self.add_cookie(self.driver)
        # # self.numeric_id = self.get_numeric_id_by_requests()
        # if self.login:
        #     self.get_numeric_id_by_selenium()

    def get_numeric_id_by_selenium(self):
        self.driver.get(self.fb_user_url)
        try:
            numeric_id = re.search(r'ecnf.\d+', self.driver.page_source).group().split(".")[-1]
        except Exception:
            numeric_id = re.search(r'"userID":"\d+"', self.driver.page_source).group().split('"')[-2]
        return numeric_id  # 100003830234443

    def get_numeric_id_by_requests(self):
        proxies = {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'
        }
        session = requests.session()
        for error_time in range(10):
            # response = requests.get(self.fb_user_url, proxies=proxies)
            response = session.get(self.fb_user_url, proxies=proxies)
            soup = BeautifulSoup(response.text, 'lxml')
            try:
                rid_url = soup.find('meta', property='al:ios:url')['content']
                numeric_id = rid_url.split('/')[-1]
                logger.info(f'Get id: {numeric_id}')
                return numeric_id
            except TypeError:  # can't find numeric id
                if soup.find('i', class_='_585p'):  # IP is banned
                    os.system('sudo killall -HUP tor')
                    logger.debug('Change IP')
                    continue
                else:  # user account does not exist
                    logger.exception('User account does not exist')

        logger.info('Exceed request limit')

    def get_numeric_id_by_lookupid(self):
        logger.info(f'Starting get numeric uid "{self.uid}" from LookUp ID URL.')
        self.driver.get(self.look_up_url)
        WebDriverWait(self.driver, 5).until(
            ec.presence_of_element_located((By.XPATH, "//input[@id='facebook_lookup_botton']")))  # Lookup button
        self.driver.find_element_by_xpath("//input[@id='input_url']").send_keys(
            f'{self.fb_base_url}{self.uid}')  # input uid url
        self.driver.find_element_by_xpath("//input[@id='facebook_lookup_botton']").click()  # send request
        WebDriverWait(self.driver, 5).until(
            ec.presence_of_element_located((By.XPATH, "//span[@id='code']")))  # wait result
        numeric_id = self.driver.find_element_by_xpath("//span[@id='code']").text  # take result
        logger.info(f'Finished get numeric uid "{self.uid}" to {numeric_id} from LookUp ID URL.')
        return numeric_id

    @staticmethod
    def get_driver():
        options = Options()
        # options.add_argument('--no-sandbox')
        # options.add_argument('--disable-dev-shm-usage')
        # options.add_argument('--headless')
        # options.add_argument('blink-settings=imagesEnabled=false')
        # options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(chrome_options=options)
        return driver

    @staticmethod
    def add_cookie(driver):
        config = configparser.RawConfigParser()
        config.read('config.ini')
        c_name = config['COOKIES']['NAME']
        c_value = config['COOKIES']['VALUE']
        c_name = c_name.split(',')
        c_value = c_value.split(',')
        driver.get('https://www.facebook.com')
        for item in zip(c_name, c_value):
            driver.add_cookie({
                'domain': '.facebook.com',
                'name': item[0],
                'value': item[1],
                'path': '/',
                'expires': None
            })
        driver.refresh()
        try:
            WebDriverWait(driver, 2).until(
                ec.presence_of_element_located((By.XPATH, '//*[text()="首頁"]')))
            login = True
        except:
            login = False
            logger.warning('AddCookieError')
        return login


def main():
    uid = 'zhongxins'
    sky = FBConvertUserID(uid=uid)


if __name__ == '__main__':
    main()
