import argparse
import codecs
from collections import defaultdict
import json
import os
import re
import sys
import time
import logging
from random import random, shuffle
try:
    from urlparse import urljoin
    from urllib import urlretrieve
except ImportError:
    from urllib.parse import urljoin
    from urllib.request import urlretrieve
import requests
from crawler.BaseCrawler import BaseCrawler
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
logger = logging.getLogger(__name__)

# HOST
HOST = "http://www.instagram.com"

# SELENIUM CSS SELECTOR
CSS_LOAD_MORE = "a._1cr2e._epyes"
CSS_RIGHT_ARROW = "//a[contains(@class, 'coreSpriteRightPaginationArrow')]"
FIREFOX_FIRST_POST_PATH = "//div[contains(@class, '_gvoze')]"
TIME_TO_CAPTION_PATH = "../../../div/ul/li/span"

# FOLLOWERS/FOLLOWING RELATED
CSS_EXPLORE = "a[href='/explore/'']"
CSS_LOGIN = "a[href='/accounts/login/']"
CSS_FOLLOWERS = "a[href='/{}/followers/']"
CSS_FOLLOWING = "a[href='/{}/following/']"
FOLLOWER_PATH = "//div[contains(text(), 'Followers')]"
FOLLOWING_PATH = "//div[contains(text(), 'Following')]"

# JAVASCRIPT COMMANDS
SCROLL_UP = "window.scrollTo(0, 0);"
SCROLL_DOWN = "window.scrollTo(0, document.body.scrollHeight);"
SCROLL_INTO_VIEW = "arguments[0].scrollIntoView();"


class InstagramCrawler(object):
    """
    Crawler class
    """

    def __init__(self):
        super().__init__()
        self.host = "http://www.instagram.com"

    def crawl(self, dir_prefix, query, crawl_type, number, caption, authentication):
        logger.debug("dir_prefix: {}, query: {}, crawl_type: {}, number: {}, caption: {}, authentication: {}"
                     .format(dir_prefix, query, crawl_type, number, caption, authentication))

        if crawl_type == "photos":
            # Browse target page
            self.browse_target_page(query)
            # Scroll down until target number photos is reached
            self.scroll_to_num_of_posts(number)

            # Scrape photo links
            self.scrape_items(number, is_hashtag=query.startswith("#"))
            # Scrape captions if specified
            if caption == True:
                self.click_and_scrape_captions(number)

        elif crawl_type in ["followers", "following"]:
            # Need to login first before crawling followers/following
            logger.info("You will need to login to crawl {}".format(crawl_type))
            self.login(authentication)

            # Then browse target page
            assert not query.startswith(
                "#"), "Hashtag does not have followers/following!"
            self.browse_target_page(query)
            # Scrape captions
            result = self.scrape_followers_or_following(crawl_type, query, number)
            if result == False:
                self.quit()
                return
        else:
            logger.warn("Unknown crawl type: {}".format(crawl_type))
            self.quit()
            return

        # Save to directory
        logger.info("Saving...")
        self.download_and_save(dir_prefix, query, crawl_type, caption)

        # Quit driver
        logger.info("Quitting driver...")
        self.quit()

    def browse_target_page(self, query):
        relative_url = query
        target_url = urljoin(HOST, relative_url)
        logger.debug("get: {}".format(urljoin(HOST, relative_url)))
        self._driver.get(target_url)

    def login(self, authentication=None):
        """
        authentication: path to authentication json file
        """
        logger.debug("get: {}".format(urljoin(HOST, "accounts/login/")))
        self._driver.get(urljoin(HOST, "accounts/login/"))

        if authentication:
            logger.info(
                "Username and password loaded from {}".format(authentication))
            with open(authentication, "r") as fin:
                auth_dict = json.loads(fin.read())
            # Input username
            username_input = WebDriverWait(self._driver, 5).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            for c in auth_dict["username"]:
                username_input.send_keys(c)
                time.sleep(random() * 0.3)
            # Input password
            time.sleep(random() * 1)
            password_input = WebDriverWait(self._driver, 5).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            for c in auth_dict["password"]:
                password_input.send_keys(c)
                time.sleep(random() * 0.3)
            # Submit
            time.sleep(random() * 1)
            password_input.submit()
        else:
            logger.warn("Type your username and password by hand to login!")
            logger.warn("You have a minute to do so!")


    def scroll_to_num_of_posts(self, number):
        # Get total number of posts of page
        num_info = re.search(r'\], "count": \d+',
                             self._driver.page_source).group()
        num_of_posts = int(re.findall(r'\d+', num_info)[0])
        logger.debug("posts: {}, number: {}".format(num_of_posts, number))
        number = number if number < num_of_posts else num_of_posts

        # scroll page until reached
        loadmore = WebDriverWait(self._driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, CSS_LOAD_MORE))
        )
        loadmore.click()

        num_to_scroll = int((number - 12) / 12) + 1
        for _ in range(num_to_scroll):
            self._driver.execute_script(SCROLL_DOWN)
            time.sleep(0.2)
            self._driver.execute_script(SCROLL_UP)
            time.sleep(0.2)

    def scrape_items(self, number, is_hashtag=False):
        logger.debug("Scraping article links...")
        encased_article_links = re.finditer(r'src="([https]+:...[\/\w \.-]*..[\/\w \.-]*'
                                          r'..[\/\w \.-]*..[\/\w \.-].jpg)', self._driver.page_source)

        article_links = [m.group(1) for m in encased_article_links]

        logger.debug("Number of article_links: {}".format(len(article_links)))

        begin = 0 if is_hashtag else 1

        self.data["article_links"] = article_links[begin:number + begin]

    def click_and_scrape_captions(self, number):
        logger.debug("Scraping captions...")
        captions = []
        datetimes = []

        posts = self._driver.find_elements_by_xpath(FIREFOX_FIRST_POST_PATH)
        shuffle(posts)
        for i, post in enumerate(posts):
            sys.stdout.write("\033[F")
            logger.debug("Scraping captions {} / {}".format(i + 1, len(posts)))
            post.click()

            # Parse caption
            datetime = ""
            try:
                time_element = WebDriverWait(self._driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "time"))
                )
                datetime = time_element.get_attribute("datetime")
                caption = time_element.find_element_by_xpath(
                    TIME_TO_CAPTION_PATH).text
            except NoSuchElementException:  # Forbidden
                logger.info("Caption not found in the {} photo".format(i + 1))
                caption = ""

            captions.append(caption)
            datetimes.append(datetime)
            # esc is only for firefox
            #time.sleep(random() * 2 + 5)
            self._driver.find_element_by_tag_name(
                "body").send_keys(Keys.ESCAPE)

            # sleep
            logger.debug("sleep...")
            time.sleep(random() * 2 + 0.3)

        self.data["captions"] = captions
        self.data["datetimes"] = datetimes

    def download_and_save(self, dir_prefix, query, crawl_type, caption):
        # Check if is hashtag
        dir_name = query.lstrip(
            "#") + ".hashtag" if query.startswith("#") else query

        dir_path = os.path.join(dir_prefix, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        logger.info("Saving to directory: {}".format(dir_path))

        # Save Photos
        for idx, photo_link in enumerate(self.data["article_links"], 0):
            sys.stdout.write("\033[F")
            logger.info("Downloading {} images to ".format(idx + 1))
            # Filename
            _, ext = os.path.splitext(photo_link)
            filename = str(idx) + ext
            filepath = os.path.join(dir_path, filename)
            # Send image request
            urlretrieve(photo_link, filepath)

        # Save Captions
        if crawl_type == "photos" and caption == True:
            filename = "captions.csv"
            filepath = os.path.join(dir_path, filename)
            with codecs.open(filepath, "w", encoding="utf-8") as f:
                for i, caption in enumerate(self.data["captions"], 0):
                    caption.replace(",", "\\COMMA")
                    c = (",%r\n" % caption)[1:-1]
                    f.write(str(self.data["datetimes"][i]) + c)

        elif crawl_type in ["followers", "following"]:
            # Save followers/following
            filename = crawl_type + ".txt"
            filepath = os.path.join(dir_path, filename)
            with codecs.open(filepath, "w", encoding="utf-8") as f:
                f.write(str(self.data["follow"]) + "\n")
                for fol in self.data[crawl_type]:
                    f.write(fol + "\n")


def main():
    # arguments
    parser = argparse.ArgumentParser(description="Instagram Crawler")
    parser.add_argument("-d", "--dir_prefix", type=str,
                        default="./data/", help="directory to save results")
    parser.add_argument("-q", "--query", type=str, default="instagram",
                        help='target to crawl, add "#" for hashtags')
    parser.add_argument("-t", "--crawl_type", type=str,
                        default="photos", help='Options: "photos" | "followers" | "following"')
    parser.add_argument("-n", "--number", type=int, default=0,
                        help="Number of posts to download: integer")
    parser.add_argument("-c", "--caption", action="store_true",
                        help="Add this flag to download caption when downloading photos")
    parser.add_argument("-l", "--headless", action="store_true",
                        help="If set, will use PhantomJS driver to run script as headless")
    parser.add_argument("-a", "--authentication", type=str, default=None,
                        help="path to authentication json file")
    args = parser.parse_args()

    crawler = Crawler(headless=args.headless)
    crawler.crawl(dir_prefix=args.dir_prefix,
                  query=args.query,
                  crawl_type=args.crawl_type,
                  number=args.number,
                  caption=args.caption,
                  authentication=args.authentication)


if __name__ == "__main__":
    main()
