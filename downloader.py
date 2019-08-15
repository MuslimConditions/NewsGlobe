import logging
import multiprocessing
import os
import time
from urllib.parse import urlparse

import feedparser
import newspaper
import requests
import simplejson as json
from bs4 import BeautifulSoup as bs

import utils

logger = logging.getLogger(__name__)

NEWS_API_KEY = ""
BING_API_KEY = ""
DEFAULT_BAR_FORMAT = " |{bar}|{n_fmt}/{total_fmt} {percentage:3.0f}% {rate_fmt}"
TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
FILE_PATH = os.path.dirname(os.path.realpath(__file__))
RSS_FEEDS = json.loads(open(os.path.join(FILE_PATH, "obj", 'rss_feeds.json'), 'rb').read())
feedparser.USER_AGENT = 'Mozilla/5.0 (Windows NT 5.1; rv:7.0.1) Gecko/20100101 Firefox/7.0.1'


class Updater:
    """Class that is used to download data and organize it.

    Articles are transferred between classes as dictionaries,
    stored in a list, in this class called self.articles.

    Every article should contain the following information:
    {'author': 'BBC Sport',
    'title': 'Some title',
    'description': 'Some longer description.',
    'url': 'http://www.bbc.co.uk/sport/cycling/123456789',
    'urlToImage': 'https://ichef.bbci.co.uk/onesport/test.jpg',
    'publishedAt': '2018-01-10T19:58:57Z'}
    """

    def __init__(self):
        logger.info('')
        self.articles = []

    def update(self, num_articles_t=None, num_feeds_max=None):
        """
        Function that downloads articles and stores them in self.articles.
        :param num_articles_t: Maximum number of articles.
        :param num_feeds_max: Maximum number of feeds.
        :return: None
        """
        logger.info('')

        self.articles = self.get_rss_feeds(num_feeds_max)
        self.articles = self.filter_articles(self.articles)
        self.articles = self.articles[:num_articles_t]

        if len(self.articles) > 0:
            print("%s new articles!" % len(self.articles))
            # TODO Enable text downloading if necessary
            # self.ArticleTextDownloader(self).download()
        else:
            print("No new articles.")

    def save_to_database(self):
        """
        Saves articles from self.articles to database.
        """
        logger.info('')
        utils.write_to_articles_database(self.articles)

    def filter_articles(self, articles):
        """
        Filters articles that are not yet in database and duplicate articles.
        :param articles: (list) List of article dictionaries.
        :return: list - Cleaned list of article dictionaries.
        """
        logger.info('')
        articles_pass = []
        urls = []
        for a_j in articles:
            url = self.lowercase_url(a_j["url"])
            if not utils.article_in_database(url):
                if url not in urls:
                    urls.append(url)
                    articles_pass.append(a_j)
        return articles_pass

    @staticmethod
    def lowercase_url(string):
        """
        Method that takes a url and converts it to lowercase.

        E.g. 'HTTP://WWW.GOOGLE.COM/ASDFGH' --> 'http://www.google.com/ASDFGH'

        Should be used only to make sure duplicate articles are not saved in database.
        :param string: str : Url to filter.
        :return: str : Filtered url.
        """
        logger.debug('')
        o = urlparse(string)
        # noinspection PyProtectedMember
        o2 = o._replace(scheme=o.scheme.lower(), netloc=o.netloc.lower())
        return o2.geturl()

    def get_rss_feeds(self, num_feeds_max):
        """
        Function that downloads RSS feeds (links are stored in RSS_FEEDS),
        and returns articles in the required format in a list.
        :param num_feeds_max: Maximum number of feeds.
        :return: Articles in a list.
        """
        logger.info('num_feeds_max:%s' % num_feeds_max)
        m = multiprocessing.Manager()
        articles = m.list()
        rss_feeds = RSS_FEEDS[:num_feeds_max]
        utils.async_getter(
            function_pointer=self.get_rss_feed,
            input_list=rss_feeds,
            pass_data={"results": articles}
        )
        return articles

    def get_rss_feed(self, url, pass_data=None):
        """
        Function that is used asynchronously to download articles from a single RSS feed.
        :param url: Url of the RSS feed.
        :param pass_data: Results list.
        :return:
        """
        logger.info(url)
        print(url)
        if pass_data:
            results = pass_data["results"]
        else:
            results = []

        feed = feedparser.parse(url)
        if 'status' in feed:
            if feed['status'] != 200:
                if feed['status'] == 301:
                    logger.warning('Feed %s has permanently moved its URL. Please check.' % url)
                else:
                    logger.critical('Error downloading feed %s, status is %s' % (url,feed['status']))
                    logger.debug(feed)
        else:
            logger.critical("Feed %s has no status, printing feed..." % url)
            logger.critical(feed)

        if 'items' in feed:
            for i in feed["items"]:
                published_at = None

                if 'published_parsed' in i:
                    if i['published_parsed'] is not None:
                        published_at = time.strftime(TIME_FORMAT, i['published_parsed'])

                if published_at is None:
                    published_at = time.strftime(TIME_FORMAT, time.gmtime())

                title = i['title']
                title = bs(title, "lxml").get_text()

                if "summary" in i:
                    description = i['summary']
                else:
                    description = ""
                description = bs(description, "lxml").get_text()

                if "worldaffairsjournal" in url:
                    description = ""

                author = feed["channel"]["title"]
                link = i['link']

                # urlToImage = i['media_thumbnail']

                results.append({'author': author,
                                'title': title,
                                'description': description,
                                'url': link,
                                'publishedAt': published_at})
        return results

    class ArticleTextDownloader:
        """
        This class is used to download articles text using newspaper module.

        Currently not used.
        """

        def __init__(self, parent):
            logger.info('')
            self.parent = parent

        def download(self):
            """
            Runs self.download_articles() and saves results to parent.articles.
            :return:
            """
            logger.info('')
            self.parent.articles = self.download_articles()

        # noinspection PyBroadException
        @staticmethod
        def download_article(a, pass_data=None):
            """
            Function that downloads a single article text.
            TODO: Check why @staticmethod needed. (Maybe self needs to be passed when @staticmethod is removed?)
            :param a: Article dictionary that contains the url.
            :param pass_data: Results dict.
            :return:
            """
            logger.info('')
            url = a["url"]

            results = pass_data["results"]
            b = newspaper.Article(url=url, fetch_images=False)
            b.download()
            try:
                b.parse()
                text = b.text

                a["text"] = text

                if a["publishedAt"] == "" or a["publishedAt"] is None:
                    a["publishedAt"] = time.strftime(TIME_FORMAT, time.gmtime())

                a['publishedAt'] = utils.clean_datetime_string(a['publishedAt'])

                results.append(a)
            except:
                print("Could not download article", url)
                pass

        def download_articles(self):
            """
            Function that downloads articles' text.
            :return: Results list.
            """
            logger.info('')
            m = multiprocessing.Manager()
            results = m.list()
            utils.async_getter(
                function_pointer=self.download_article,
                input_list=self.parent.articles,
                pass_data={"results": results},
            )
            return results
