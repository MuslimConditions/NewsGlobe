import datetime
import glob
import json
import logging
import multiprocessing
import os
import time
from functools import partial

import peewee

import objects

logger = logging.getLogger(__name__)

# TAGGER_PID = None
ARTICLES_DB = objects.DATABASE_LOCATION
TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

FILE_PATH = os.path.dirname(os.path.realpath(__file__))


class Stopwatch:
    """
    Stopwatch. Times and prints code run time in seconds.
    Start the stopwatch with initializiation:
    s = Stopwatch()
    Time the laps using
    s.lap("String to print")
    """

    def __init__(self):
        self.time_last = time.time()

    def lap(self, string_to_print):
        time_now = time.time()
        time_dif = time_now - self.time_last
        self.time_last = time_now
        print(string_to_print, time_dif)


def async_getter(function_pointer=None, input_list=None, pass_data=None, processes=4, timeout=5):
    logger.info(function_pointer)
    """
    Function that is used to provide easier functionality of asynchronous processes.
    You can use it in applications with a single list of items that need to be processed
    and that need to be put into a single list of output items.

    Example:
        def async_process():
            m = multiprocessing.Manager()
            results = m.list()
            async_getter(
                function_pointer=function,
                input_list=[1,2,3],
                pass_data={"results": results}
            )
            return results

        def function(list_item, pass_data=None):
            results = pass_data["results"]
            a = 1+list_item
            results.append(a)


    :param function_pointer: Function that async getter asynchronously starts.
    :param input_list: List of items that should be fed to function.
    :param pass_data: Additional data that should be fed to function (e.g. combined output).
    :param processes: Number of spawned asynchronous processes.
    :param progress_bar: Enables progress bar (which works only with Pool function - not ThreadPool).
    :param bar_format: Overrides progress bar look.
    :param timeout: Maximum allowed time to finish single async process in seconds.
    :return: TODO: define return
    """

    function_pointer = partial(function_pointer, pass_data=pass_data)
    p = multiprocessing.pool.ThreadPool(processes)
    p.map(partial(abortable_worker, function_pointer, timeout=timeout), input_list)
    p.terminate()


def abortable_worker(func, *args, **kwargs):
    logger.info(func)
    """
    Helper function of async_getter that enables easier timeout handling.
    :param func: Function that operates asynchronously.
    :param args: Function arguments.
    :param kwargs: Function keyword arguments.
    :return: Returns apply_async().get() .
    """
    timeout = kwargs.get('timeout', None)
    p = multiprocessing.pool.ThreadPool(1)
    res = p.apply_async(func, args=args)
    try:
        out = res.get(timeout)  # Wait timeout seconds for func to complete.
        return out
    except multiprocessing.TimeoutError:
        p.terminate()


def create_articles_database():
    logger.info('')
    """
    Creates an article database if it does not exist.
    """
    db = peewee.SqliteDatabase(objects.DATABASE_LOCATION)
    db.connect()
    if not objects.ArticleObject.table_exists():
        db.create_tables([objects.ArticleObject])
    db.close()


def write_to_articles_database(list_of_article_dicts):
    logger.info('')
    """
    Inserts a list of articles into the article database.
    Use with large lists.
    :param list_of_article_dicts: Self-explanatory.
    :return:
    """
    db = peewee.SqliteDatabase(ARTICLES_DB)
    db.connect()

    articles = [(j["url"], json.dumps(j)) for j in list_of_article_dicts]
    articles_to_write = []

    for a in articles:
        url = a[0]
        jsn = a[1]
        if not article_in_database(url):
            articles_to_write.append({"url": url, "json": jsn})

    with db.atomic():
        for idx in range(0, len(articles_to_write), 100):
            objects.ArticleObject.insert_many(articles_to_write[idx:idx + 100]).execute()
    db.close()


def get_article_from_database(url):
    logger.info('')
    """
    Gets single article from database.
    :param url: Unique article url.
    :return: Returns article object.
    """
    db = peewee.SqliteDatabase(ARTICLES_DB)
    db.connect()
    article = objects.ArticleObject.get(objects.ArticleObject.url == url)
    db.close()
    return article


def article_in_database(article_url):
    logger.debug('')
    """
    Returns true if article_url is in database, else false.
    :param article_url: Unique article url.
    :return: Boolean.
    """
    db = peewee.SqliteDatabase(ARTICLES_DB)
    db.connect()
    query = objects.ArticleObject.select().where(objects.ArticleObject.url == article_url)
    db.close()
    if query.exists():
        return True
    else:
        return False


def string_to_date(string):
    logger.debug('')
    """
    Converts string to datetime object.
    :param string: Date string.
    :return: datetime object.
    """
    return datetime.datetime.strptime(string, TIME_FORMAT)


def date_to_string(date, time_format=TIME_FORMAT):
    logger.debug('')
    """
    Converts string to datetime object.
    :param date: date object
    :return: String object.
    """
    return datetime.datetime.strftime(date, time_format)


def clean_datetime_string(string):
    logger.info('')
    """
    Cleans and formats date strings.
    :param string: Date string
    :return: Formatted date string.
    """
    if "+" in string:
        string = string.split("+")[0]
    if "." in string:
        string = string.split(".")[0]
    if "Z" not in string:
        string = string + "Z"
    return string


def get_article_daterange(date_from, date_to):
    logger.info('')
    """
    Gets article list for articles ranging from (not including) date_from
    to (not including) date to.
    :param date_from: date_object
    :param date_to: date_object
    :return: list of article dictionaries.
    """
    out = []
    for a in objects.ArticleObject.select():
        a_json = json.loads(a.json)
        published_at = a_json['publishedAt']
        published_at_date = string_to_date(published_at)

        if date_from < published_at_date < date_to:
            out.append(json.loads(a.json))
    return out


def clean_date_strings():
    logger.info('')
    """
    Cleanes database of incorrectly formatted dates.
    """
    articles_in_db = objects.ArticleObject.select()
    num_articles = len(articles_in_db)
    print("cleaning", num_articles, "articles")
    i = 0
    for a in articles_in_db:
        i += 1
        a_json = json.loads(a.json)
        if "publishedAt" in a_json:
            published_at = a_json['publishedAt']
            published_clean = clean_datetime_string(published_at)
            if published_clean != published_at:
                a_json['publishedAt'] = published_clean
                to_write_json = json.dumps(a_json)
                a.json = to_write_json
                a.save()
        else:
            print(a.json)
            a.delete_instance()


def get_next_midnight(timedelta=0):
    logger.info('')
    """
    Returns next midnight (as datetime object) + timedelta (in days).
    :param timedelta: Integer : number of days.
    :return: datetime object.
    """
    # Defaults to today at midnight
    date_now = datetime.datetime.now()
    date_today_midnight = date_now.replace(hour=0, minute=0, second=0, microsecond=0)
    date_from = date_today_midnight + datetime.timedelta(days=timedelta)
    return date_from


def parse_date_str(date_str=None, default_timedelta=0):
    logger.info('')
    """
    Parses date string and tries to return datetime object.
    If input string equals None, it returns get_next_midnight(default_timedelta).
    TODO: Check if that is correct behaviour.
    :param date_str: String : formatted date.
    :param default_timedelta:  Integer : number of days to add.
    :return: datetime object.
    """
    if not date_str:
        date = get_next_midnight(default_timedelta)
    else:
        date = string_to_date(date_str)
    return date


def clean_string(string):
    logger.debug('')
    """
    Cleans string.
    Removes non-alphanumeric characters. Strips extra whitespace.
    :param string: Input string.
    :return: Output string.
    """
    string = "".join([c if c.isalnum() or c == " " else "" for c in string])
    string = string.strip()
    string = ' '.join(string.split())
    return string


def delete_location_logs():
    logger.info('')
    list_of_files = glob.glob(os.path.join(
        FILE_PATH, "logs", "locations", "*.log"))
    files_to_delete = sorted(list_of_files, key=os.path.getctime, reverse=True)[1:]
    i = 0
    for f in files_to_delete:
        os.remove(f)
        i += 1

    if i > 0:
        print("Deleted", i, "old location logs!")
    return
