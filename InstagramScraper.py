#! /usr/bin/env python3
# Instagram Scraper
# Coded by sc1341 
# http://github.com/sc1341/InstagramOSINT
# I am not responsible for anything you do with this script
# This is mean to be imported as a python module for use in custom applications
#
#

from bs4 import BeautifulSoup
import json
import os
import re
import requests
import random
import string
import sys
import time
import logging
from logging.config import fileConfig
from distutils.util import strtobool
import datetime
from urllib import parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options

fileConfig('config.ini')
logger = logging.getLogger('InstagramScraper_Log:')


class InstagramScraper:

    def __init__(self, username):
        self.username = username
        self.home_url = 'https://instagram.com/'
        self.base_url = 'https://www.instagram.com/graphql/query/?query_hash=7c8a1055f69ff97dc201e752cf6f0093&variables='
        self.useragents = [
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14',
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0']
        self.driver_cookie = 'ig_did=B4E1A0FB-2EA5-4CBB-ACE4-97F52DD4F9E5; mid=XuYtuAALAAG6cySsWjVwdZrbV_pz; csrftoken=TLmz63hced4AmLsGWi6PiHmytuG0Hura; ds_user_id=37053622625; sessionid=37053622625%3AxoU3p38tya4Vi6%3A21; shbid=17564; shbts=1592143308.0574408; rur=FRC; urlgen="{\"36.224.101.169\": 3462\054 \"211.72.111.251\": 3462}:1jl789:c82dn2rQIU9G6_tyVOqJ9BRo5Qk'
        self.cookies = {'sessionid': '37053622625%3Awj4RlpGgrXcSiP%3A10'}
        self.profile_data, self.profile_meta = self.scrape_profile()

    def __getitem__(self, i):
        return self.profile_data[i]

    def scrape_profile(self):
        """
        This is the main scrape which takes the profile data retrieved and saves it into profile_data
        :return: profile data
        :param: none
        """
        # Get the html data with the requests module
        logger.info(f"{colors.OKGREEN}Starting scan on {self.username}{colors.ENDC}")
        response = self.get_response(f'{self.home_url}{self.username}')
        soup = BeautifulSoup(response.text, 'lxml')
        # Find the tags that hold the data we want to parse
        general_data = soup.find_all('meta', attrs={'property': 'og:description'})
        more_data = soup.find_all('script', attrs={'type': 'text/javascript'})
        # description = soup.find('script', attrs={'type': 'application/ld+json'})
        # Try to parse the content -- if it fails then the program exits
        try:
            text = general_data[0].get('content').split()
            # description = json.loads(re.search(r'{(...)+', str(description)).group())
            profile_meta = json.loads(re.search(r'{(...)+', str(more_data[3])).group().strip(';</script>'))
        except:
            logger.warning(f'{colors.FAIL}Username "{self.username}" not found{colors.ENDC}')
            return 1
        profile_data = {
            "Username": profile_meta['entry_data']['ProfilePage'][0]['graphql']['user']['username'],
            "User_id": profile_meta['entry_data']['ProfilePage'][0]['graphql']['user']['id'],
            "Profile name": profile_meta['entry_data']['ProfilePage'][0]['graphql']['user']['full_name'],
            "URL": f'{self.home_url}{self.username}',
            "Followers": profile_meta['entry_data']['ProfilePage'][0]['graphql']['user']['edge_followed_by']['count'],
            "Following": profile_meta['entry_data']['ProfilePage'][0]['graphql']['user']['edge_follow']['count'],
            "Posts": text[4],
            "Bio": str(profile_meta['entry_data']['ProfilePage'][0]['graphql']['user']['biography']),
            "profile_pic_url": str(
                profile_meta['entry_data']['ProfilePage'][0]['graphql']['user']['profile_pic_url_hd']),
            "is_business_account": str(
                profile_meta['entry_data']['ProfilePage'][0]['graphql']['user']['is_business_account']),
            "connected_to_fb": str(
                profile_meta['entry_data']['ProfilePage'][0]['graphql']['user']['connected_fb_page']),
            "external_url": str(profile_meta['entry_data']['ProfilePage'][0]['graphql']['user']['external_url']),
            "joined_recently": str(
                profile_meta['entry_data']['ProfilePage'][0]['graphql']['user']['is_joined_recently']),
            "business_category_name": str(
                profile_meta['entry_data']['ProfilePage'][0]['graphql']['user']['business_category_name']),
            "is_private": str(profile_meta['entry_data']['ProfilePage'][0]['graphql']['user']['is_private']),
            "is_verified": str(profile_meta['entry_data']['ProfilePage'][0]['graphql']['user']['is_verified']),
            "Page_Cursor":
                profile_meta['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media'][
                    'page_info'][
                    'end_cursor'],
        }
        logger.info(f'{colors.OKBLUE}Finished scan on "{self.username}" profile{colors.ENDC}')

        return profile_data, profile_meta

    def scrape_posts(self):
        """
        Scrapes all posts and downloads them
        :return: none
        :param: none
        """
        if strtobool(self.profile_data["is_private"]):
            logger.info(f'{colors.FAIL} This account "{self.username}" is private')
            return 1
        logger.info(f'{colors.OKGREEN}Starting scan on {self.username} posts')
        if strtobool(self.profile_data['is_private']):
            logger.warning(f"{self.username} is private profile, cannot scrape photos!")
            # save profile is private
            return 1
        else:
            posts = {}
            index = 0
            next_page_cursor = self.profile_data["Page_Cursor"]
            post_data = \
                self.profile_meta['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media'][
                    'edges']
            while post_data:
                for post in post_data:
                    os.mkdir(str(index))
                    posts[index] = {"Post URL": f'{self.home_url}p/{post["node"]["shortcode"]}',
                                    "Post Type": post['node']['__typename'],
                                    "Comments": post['node']['edge_media_to_comment']['count'],
                                    "Comments Disabled": str(post['node']['comments_disabled']),
                                    "DateTime": datetime.datetime.fromtimestamp(post['node']['taken_at_timestamp']),
                                    # "Likes": post['node']['edge_liked_by']['count'],
                                    # "Accessability Caption": str(post['node']['accessibility_caption']),
                                    }
                    # get post message but maybe dont have message in post
                    try:
                        posts[index].update({"Message": str(
                            post['node']['edge_media_to_caption']['edges'][0]['node']['text']).replace('\n', '')})
                    except:
                        posts[index].update({"Message": ''})
                    # get post likes count(only first 12 posts can get likes count now)
                    post_profile_meta, interaction_count = self.get_profile_in_post(posts[index]['Post URL'])
                    # posts[index].update({"Likes": post['node']['edge_liked_by']['count']})
                    posts[index].update({"Interaction Count": interaction_count})
                    pic_or_video_url = []
                    if posts[index]["Post Type"] == 'GraphImage':  # only one pic
                        pic_or_video_url = post['node']['display_url']
                        # posts[index].update({"The Photo 1 URL": post['node']['display_url']})
                        self.download_post_picture_or_video(index, pic_or_video_url, '.jpg')
                    elif posts[index]["Post Type"] == 'GraphSidecar':  # more than 2 pics
                        for photo_index, edge in enumerate(post['node']['edge_sidecar_to_children']['edges']):
                            pic_or_video_url.append(edge['node']['display_url'])
                            # posts[index].update({f"The Photo/Video {photo_index} URL": edge['node']['display_url']})
                            self.download_post_picture_or_video(index, pic_or_video_url[photo_index], '.jpg')
                    elif posts[index]["Post Type"] == 'GraphVideo':
                        pic_or_video_url = post_profile_meta['entry_data']['PostPage'][0]['graphql'][
                            'shortcode_media']['video_url']
                        # posts[index].update({"The Video URL": post_profile_meta['entry_data']['PostPage'][0]['graphql'][
                        #     'shotcode_media']['video_url']})
                        self.download_post_picture_or_video(index, pic_or_video_url, '.mp4')
                    posts[index].update({"Pic(s) or Video URL:": pic_or_video_url})
                    # save the post text
                    with open(f'{os.getcwd()}/{index}/post_info.txt', 'w', encoding="utf-8") as f:
                        f.write(str(posts[index]))
                    if not strtobool(posts[index]['Comments Disabled']):
                        self.get_comment_from_post(index, posts[index]["Post URL"])
                    index += 1
                # The Next Page For 12 Posts
                if next_page_cursor is not None:
                    var_num = {"id": self.profile_data.get('User_id'), "first": '12',
                               "after": next_page_cursor}
                    var_num_code = parse.quote(json.dumps(var_num))
                    next_response = self.get_response(f'{self.base_url}{var_num_code}')
                    post_data = json.loads(next_response.text)['data']['user']['edge_owner_to_timeline_media']['edges']
                    next_page_cursor = \
                        json.loads(next_response.text)['data']['user']['edge_owner_to_timeline_media']['page_info'][
                            'end_cursor']
                else:
                    break

    def get_comment_from_post(self, index, post_url):
        """
        Get all comment in each post
        :param post_url:
        :return:
        """
        # post_response = self.get_response(post_url)
        # soup = BeautifulSoup(post_response.text, 'lxml')
        # more_data_in_comments = soup.find_all('script', attrs={'type': 'text/javascript'})
        # comments_data = json.loads(re.search(r'{(...)+', str(more_data_in_comments[3])).group().strip(';</script>'))
        # comments = comments_data['entry_data']['PostPage'][0]['graphql']['shortcode_media']['edge_media_to_parent_comment']['edges']
        # next_page_cursor = comments[0]['node']['edge_threaded_comments']['page_info']['end_cursor']
        # while comments:
        #     for comment in comments:
        #         text = comment['node']['text']
        #         created_time = datetime.datetime.fromtimestamp(comment['node']['created_at'])
        #         user_name = comment['node']['owner']['username']
        #         print(f'{user_name}: {text}')
        #         var_num = {"id": self.profile_data.get('User_id'), "first": '80',
        #                    "after": next_page_cursor}
        #         var_num_code = parse.quote(json.dumps(var_num))
        #         next_comments_response = self.get_response(f'{self.base_url}{var_num_code}')
        #         post_data = json.loads(next_comments_response.text)['data']['user']['edge_owner_to_timeline_media']['edges']
        #         next_page_cursor = \
        #             json.loads(next_comments_response.text)['data']['user']['edge_owner_to_timeline_media']['page_info'][
        #                 'end_cursor']
        #         if next_page_cursor is None:
        #             break
        # logger.info(f'{colors.OKGREEN}Finished scan on {self.username} posts')
        logger.info(f'{colors.OKGREEN}Starting scan on {self.username}:{post_url}{colors.ENDC}')
        driver = self.get_driver()
        driver.get(post_url)
        comments_count = 0
        while True:
            try:
                WebDriverWait(driver, 4, 0.5).until(
                    ec.visibility_of_element_located((By.CSS_SELECTOR, ('.dCJp8')))).click()
                soup = BeautifulSoup(driver.page_source, 'lxml')
                comments_len = len(soup.find_all('ul', class_='Mr508'))
                if comments_len == comments_count:
                    break
            except:
                logger.exception(f'{colors.FAIL}STH error in expand comments{colors.ENDC}')
                break
        soup = BeautifulSoup(driver.page_source, 'lxml')
        try:
            all_comments = soup.find_all('ul', class_='Mr508')
            comment_info = {}
            comment_index = 1
            for comment in all_comments:
                comment_row = comment.find('div', class_='C4VMK', recursive=True)
                comment_info[comment_index] = {"User Name": comment_row.find('a', href=True).text}
                comment_info[comment_index].update({"Comment Message": comment_row.find('span', class_="").text})
                created_time = re.search(r'datetime="(...)+"', str(comment_row.find('time', datetime=True))).group().split('"')[1]
                created_time = datetime.datetime.strptime(created_time[:-5], '%Y-%m-%dT%H:%M:%S')
                comment_info[comment_index].update({"Comment Created Time": created_time})
                comment_index += 1

                with open(f'{os.getcwd()}/{index}/comment_info.txt', 'w', encoding="utf-8") as f:
                    f.write(str(comment_info))
        except:
            logger.exception(f'{colors.FAIL}STH error in comments scrap{colors.ENDC}')
        logger.info(f'{colors.OKGREEN}Finished scan on {self.username}:{post_url}{colors.ENDC}')

    def make_directory(self):
        """
        Makes the profile directory and changes the cwd to it
        this should only be called from the save_data function!
        :return: True
        """
        try:
            os.mkdir(self.username)
            os.chdir(self.username)
        except FileExistsError:
            num = 0
            while os.path.exists(self.username):
                num += 1
                try:
                    os.mkdir(self.username + '-' + str(num))
                    os.chdir(self.username + '-' + str(num))
                except FileExistsError:
                    pass

    def save_data(self):
        """
        Saves the data to the username directory
        :return: none
        """
        self.make_directory()
        with open('data.txt', 'w') as f:
            f.write(json.dumps(self.profile_data))
        # Downloads the profile Picture
        self.download_profile_picture()
        print(f"Saved data to directory {os.getcwd()}")

    def print_profile_data(self):
        """
        Prints out the data to the screen by iterating through the dict with it's key and value
        :return: none
        """
        # Print the data out to the user
        print(colors.HEADER + "---------------------------------------------" + colors.ENDC)
        print(colors.OKGREEN + f"Results: scan for {self.profile_data['Username']} on instagram" + colors.ENDC)
        for key, value in self.profile_data.items():
            print(key + ':' + value)

    def get_driver(self):
        """
        get driver and login with cookie
        :return: driver
        """
        driver = webdriver.Chrome()
        driver.get(self.home_url)
        cookie = self.driver_cookie
        cookie_data = cookie.split('; ')
        for item in cookie_data:
            item = item.split('=')
            driver.add_cookie({
                'domain': '.instagram.com',
                'name': item[0],
                'value': item[1],
                'path': '/',
                'expires': None
            })
        driver.refresh()
        return driver

    def get_response(self, url):
        """
        get response from requests
        :param url:
        :return: True
        """
        try:
            response = requests.get(url=url, headers={'User-Agent': random.choice(self.useragents)},
                                    cookies=self.cookies)
        except:
            logger.warning(f'{colors.FAIL} Get {url} response fail{colors.ENDC}')
            return 1
        return response

    def download_profile_picture(self):
        """
        Downloads the profile pic and saves it to the directory
        :return: none
        """
        with open("profile_pic.jpg", "wb") as f:
            time.sleep(1)
            profile_picture_url = self.get_response(self.profile_data['profile_pic_url'])
            f.write(profile_picture_url.content)

    def download_post_picture_or_video(self, index, url, download_type):
        """
        Downloads the post pic(s) and saves it to directory
        :param index: which pic in post
        :param url: each pic url
        :param download_type: if is pic = .jpg elif video = .mp4
        :return: none
        """
        with open(f'{os.getcwd()}/{index}/' + ''.join(
                [random.choice(string.ascii_uppercase) for x in range(random.randint(1, 9))]) + f'{download_type}',
                  'wb') as f:
            time.sleep(random.randint(5, 10))
            pic_or_video_response = self.get_response(url)

            f.write(pic_or_video_response.content)

    def get_profile_in_post(self, url):
        """
        Get profile from each post
        :param url: post url
        :return: True
        """
        logger.info(f'{colors.OKGREEN}{url} starting to get post profile')
        post_response = self.get_response(url)
        soup = BeautifulSoup(post_response.text, 'lxml')
        profile = soup.find_all('script', attrs={'type': 'text/javascript'})
        post_profile_meta = json.loads(re.search(r'{(...)+', str(profile[3])).group().strip(';</script>'))
        description = soup.find('script', attrs={'type': 'application/ld+json'})
        try:
            description = json.loads(re.search(r'{(...)+"*}*', str(description)).group())
            interaction_count = description['interactionStatistic']['userInteractionCount']
        except AttributeError:
            interaction_count = \
            post_profile_meta['entry_data']['PostPage'][0]['graphql']['shortcode_media']['edge_media_preview_like'][
                'count']
        except:
            interaction_count = 0
            logger.exception(f'{colors.FAIL}{url} get interaction count fail{colors.ENDC}')
        logger.info(f'{colors.OKBLUE}{url} finished get post profile')
        return post_profile_meta, interaction_count


def main(username):
    print(f'{colors.HEADER}{banner}{colors.ENDC}')
    profile = InstagramScraper(username=username)
    save_profile = profile.save_data()
    profile_post = profile.scrape_posts()
    # post_comments = profile.get_comment_from_post()


if __name__ == '__main__':
    main('ku.william')
