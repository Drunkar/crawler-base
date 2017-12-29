from collections import defaultdict
import logging
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
logger = logging.getLogger(__name__)


class BaseCrawler(object):
    def __init__(self):
        self._driver = webdriver.Remote(
            command_executor="http://127.0.0.1:4444/wd/hub",
            desired_capabilities=DesiredCapabilities.CHROME)
        self.data = defaultdict(list)

    def quit(self):
        self._driver.quit()
