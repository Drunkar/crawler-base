import re
import os
import time
import json
import codecs
from datetime import datetime
from random import random
import logging
from crawler.BaseCrawler import BaseCrawler
try:
    from urlparse import urljoin
    from urllib import urlretrieve
except ImportError:
    from urllib.parse import urljoin
    from urllib.request import urlretrieve
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
logger = logging.getLogger(__name__)


class RedditCrawler(BaseCrawler):
    def __init__(self):
        super().__init__()
        self.host = "https://www.reddit.com/"

    def crawl(self, dir_prefix, query, crawl_type, number, caption, authentication):
        logger.debug("dir_prefix: {}, query: {}, crawl_type: {}, number: {}, caption: {}, authentication: {}"
                     .format(dir_prefix, query, crawl_type, number, caption, authentication))

        if crawl_type == "feed":
            self.login(query, authentication)

            # Scrape article links
            self.scrape_items(number)

            # Scrape captions if specified
            if caption == True:
                self.click_and_scrape_captions(number)

        else:
            self.quit()
            raise Exception("Unknown crawl type: {}".format("/"))
            return

        # Save to directory
        logger.info("Saving...")
        self.download_and_save(dir_prefix, query, crawl_type, caption)

        # Quit driver
        logger.info("Quitting driver...")
        self.quit()

    def login(self, query, authentication=None):
        """
        authentication: path to authentication json file
        """
        logger.debug("get: {}".format(urljoin(self.host, query)))
        self._driver.get(urljoin(self.host, query))

        if authentication:
            logger.info(
                "Username and password loaded from {}".format(authentication))
            with open(authentication, "r") as fin:
                auth_dict = json.loads(fin.read())
            # Input username
            username_input = WebDriverWait(self._driver, 5).until(
                EC.presence_of_element_located((By.NAME, "user"))
            )
            for c in auth_dict["username"]:
                username_input.send_keys(c)
                time.sleep(random() * 0.3)
            logger.debug("input username finished")
            # Input password
            time.sleep(random() * 1)
            password_input = WebDriverWait(self._driver, 5).until(
                EC.presence_of_element_located((By.NAME, "passwd"))
            )
            for c in auth_dict["password"]:
                password_input.send_keys(c)
                time.sleep(random() * 0.3)
            logger.debug("input password finished")
            # Submit
            time.sleep(random() * 1)
            logger.debug("submit")
            password_input.submit()
        else:
            logger.warn("Type your username and password by hand to login!")
            logger.warn("You have a minute to do so!")
        time.sleep(5)
        WebDriverWait(self._driver, 15).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "p[class='title']"))
        )

    def scrape_items(self, number):
        logger.debug("Scraping article links...")
        encased_article_links = re.finditer(
            r'data-url="([^"]*)"', self._driver.page_source)
        article_links = [m.group(1) for m in encased_article_links]
        article_links = [l if l.startswith(
            "http://") or l.startswith("https://") else urljoin(self.host, l) for l in article_links]

        logger.debug("Number of article_links: {}".format(len(article_links)))
        logger.debug(article_links)
        self.data["article_links"] = article_links

    def download_and_save(self, dir_prefix, query, crawl_type, caption):
        dir_path = dir_prefix
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        logger.debug("Saving to directory: {}".format(dir_path))
        filename = "feed_{}.csv".format(
            datetime.now().strftime("%Y%m%d_%H%M%S"))
        filepath = os.path.join(dir_path, filename)
        with codecs.open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(self.data["article_links"]) + "\n")
