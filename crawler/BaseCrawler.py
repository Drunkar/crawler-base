from collections import defaultdict
import logging
import os
import random
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
from fake_useragent import UserAgent
logger = logging.getLogger(__name__)


ua = UserAgent()

class BaseCrawler(object):
    def __init__(self, executor_address, with_proxy, conn_check_url, conn_check_xpath):
        self.retries = 3
        self.timeout = 10
        self.executor_address = executor_address
        self.conn_check_url = conn_check_url
        self.conn_check_xpath = conn_check_xpath
        self.flags = ["start-maximized", "--no-sandbox", "--disable-infobars", "--disable-dev-shm-usage", "--disable-browser-side-navigation", "--disable-gpu"]
        if with_proxy:
            # get free proxy list
            proxies = self.get_proxies()
            logger.info("{} proxies loaded.".format(len(proxies)))
            self.launch_proxy_webdriver(proxies)
        else:
            self.launch_webdriver()

        self.data = defaultdict(list)

    def get_proxies(self):
        logging.info("Loading proxies....")
        proxies = []
        if os.path.isfile("proxies.txt"):
            logging.info("loading proxies from local file.")
            with open("proxies.txt", "r") as f:
                for line in f:
                    if ":" in line:
                        proxies.append(line.strip())
            return proxies

        logging.info("get free proxies from web.")
        driver = webdriver.Remote(
            command_executor=self.executor_address,
            desired_capabilities=webdriver.DesiredCapabilities.CHROME)
        driver.set_page_load_timeout(35)
        driver.get("https://www.sslproxies.org/")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tr[role='row']"))
        )

        # select 'Show 80 entries'
        element = driver.find_element_by_name("proxylisttable_length")
        Select(element).select_by_value("80")

        for p in driver.find_elements_by_css_selector("tr[role='row']"):
            result = p.text.split(" ")
            if result[-1] == "yes":
                proxies.append(result[0]+":"+result[1])

        driver.close()
        driver.quit()
        return proxies

    def launch_proxy_webdriver(self, proxies):
        for ip in random.sample(proxies, len(proxies)):
            proxy = Proxy()
            proxy.proxy_type = ProxyType.MANUAL
            proxy.http_proxy = ip
            proxy.ssl_proxy = ip
            proxy.no_proxy = None
            self.capabilities = webdriver.DesiredCapabilities.CHROME
            proxy.add_to_capabilities(self.capabilities)
            logger.debug("selected proxy: {}".format(ip))
            # set useragent
            u = ua.random
            self.capabilities["chrome_options"] = {"args": ["--user-agent=" + u] + self.flags}
            logger.info("ua: {}".format(u))
            self._driver = webdriver.Remote(
                command_executor=self.executor_address,
                desired_capabilities=self.capabilities)
            self._driver.set_page_load_timeout(self.timeout)
            if self.has_internet_connection():
                logger.info("Using ip: {}".format(ip))
                self.ip = ip
                return
            else:
                self.quit()
                time.sleep(4)
        raise Exception("Error: No valid ip found.")

    def launch_webdriver(self):
        self.capabilities = webdriver.DesiredCapabilities.CHROME
        # set useragent
        u = ua.random
        self.capabilities["chrome_options"] = {"args": ["--user-agent=" + u] + self.flags}
        logger.info("ua: {}".format(u))
        self._driver = webdriver.Remote(
            command_executor=self.executor_address,
            desired_capabilities=self.capabilities)
        self._driver.set_page_load_timeout(self.timeout)

    def change_ua(self):
        self.quit()
        proxy = Proxy()
        proxy.proxy_type = ProxyType.MANUAL
        proxy.http_proxy = self.ip
        proxy.ssl_proxy = self.ip
        proxy.no_proxy = None
        self.capabilities = webdriver.DesiredCapabilities.CHROME
        proxy.add_to_capabilities(self.capabilities)
        # set useragent
        u = ua.random
        self.capabilities["chrome_options"] = {"args": ["--user-agent=" + u] + self.flags}
        logger.info("ua: {}".format(u))
        self._driver = webdriver.Remote(
            command_executor=self.executor_address,
            desired_capabilities=self.capabilities)
        self._driver.set_page_load_timeout(self.timeout)

    def get_current_url(self):
        return self._driver.current_url

    def has_internet_connection(self):
        has_connection = False
        self._driver.set_page_load_timeout(15)
        try:
            self._driver.get(self.conn_check_url)
            WebDriverWait(self._driver, 8).until(
                EC.presence_of_element_located(
                    (By.XPATH, self.conn_check_xpath))
            )
            has_connection = True
            self.recreate_webdriver_connection()
            return True
        except TimeoutException:
            self.recreate_webdriver_connection()
            if has_connection:
                return True
            else:
                return False
        return True

    def get(self, url):
        i = 0
        while i < self.retries:
            self._driver.delete_all_cookies()
            try:
                self._driver.get(url)
            except TimeoutException:
                i = i + 1
                logger.warn("Timeout, Retrying... ({}/{})".format(i, self.retries))
                self.recreate_webdriver_connection()
                time.sleep(random.random() * 5.0)
                continue
            else:
                return
        raise TimeoutException("Page was not loaded in time({}s sec).".format(self.timeout))

    def get_wait_xpath(self, url, xpath, timeout):
        self._driver.set_page_load_timeout(timeout+2)
        i = 0
        while i < self.retries:
            self._driver.delete_all_cookies()
            try:
                self._driver.get(url)
                WebDriverWait(self._driver, timeout).until(
                    EC.presence_of_element_located(
                        (By.XPATH, xpath))
                )
            except TimeoutException:
                i = i + 1
                logger.warn("Timeout, Retrying... ({}/{})".format(i, self.retries))
                self.recreate_webdriver_connection()
                time.sleep(random.random() * 5.0)
                continue
            else:
                return
        raise TimeoutException("Page was not loaded in time({}s sec).".format(timeout+2))


    def recreate_webdriver_connection(self):
        self.quit()
        self._driver = webdriver.Remote(
            command_executor=self.executor_address,
            desired_capabilities=self.capabilities)
        self._driver.set_page_load_timeout(self.timeout)

    def quit(self):
        self._driver.close()
        self._driver.quit()
