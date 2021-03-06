import argparse
from datetime import datetime, timedelta
import logging
import traceback
import util
import sys
from crawler.RedditCrawler import RedditCrawler

logger = logging.getLogger()

def main(args, executor_address):
    try:
        crawler = RedditCrawler(executor_address, args.with_proxy)
        crawler.crawl(dir_prefix="./data/",
                      query="/",
                      crawl_type="feed",
                      number=256,
                      caption=False,
                      authentication="auth.json")
    except Exception as e:
        logger.warn(e)
        trc = traceback.format_exc()
        logger.warn(trc)
    finally:
        crawler.quit()


if __name__ == '__main__':
    # args
    parser = argparse.ArgumentParser(
        description="Crowl examlple.")
    parser.add_argument(
        "--with-proxy", action="store_true", help="Debug mode.")
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Debug mode.")
    args = parser.parse_args()

    # logger
    if args.debug:
        LOG_LEVEL = logging.DEBUG
    else:
        LOG_LEVEL = logging.INFO
    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)s [%(name)s/%(funcName)s() at line %(lineno)d]: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    logger.setLevel(LOG_LEVEL)
    # stdout
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(LOG_LEVEL)
    logger.addHandler(stream_handler)

    start = datetime.now()
    logger.info("Start crawling: " + start.strftime("%Y-%m-%d %H:%M:%S"))

    env_file = "local.env"
    executor_address = util.get_executor_address(env_file)
    main(args, executor_address)

    end = datetime.now()
    logger.info("End crawling: " + end.strftime("%Y-%m-%d %H:%M:%S"))
    polling_time = end - start
    logger.info("polling time[min]: " +
                str(polling_time.total_seconds() / 60.0))
