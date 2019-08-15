#!/bin/python
import argparse
import datetime
import logging

import email_sender
from web_app import ftp_upload
import periodic_updater
import utils
import downloader
import parsing

logger = logging.getLogger(__name__)
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"


def get_articles_range(a_range, num_articles, **kwargs):
    """
    This function serves as the main function.
    1. Calls downloader.Updater.update() and saves new articles from the web into the database
    2. Calls parsing.Parser.parse_date_range() that collects the latest news from the database and parses it into JSON,
        that is then read by the JavaScript Cesium application and displayed in the browser.
    :param a_range: Days before next midnight to parse.
    :param num_articles: Maximum number of articles to be parsed.
    :param kwargs: Other arguments
    :return: Returns list of Updater and Parser instances.
    """

    global downloader
    global parsing

    logger.info('')

    # For handling test case
    if "test" in kwargs:
        downloader = kwargs.get("downloader")
        parsing = kwargs.get("parsing")

    print("Getting article range...")
    u = downloader.Updater()
    u.update(num_articles)
    u.save_to_database()
    p = parsing.Parser()
    p.parse_date_range(timedelta=a_range)

    if "ftp_host" in kwargs and "ftp_username" in kwargs and "ftp_password" in kwargs:
        if kwargs["ftp_host"] and kwargs["ftp_username"] and kwargs["ftp_password"]:
            ftp_upload.update_all_files(ftp_host=kwargs["ftp_host"],
                                        ftp_port=kwargs["ftp_port"],
                                        ftp_username=kwargs["ftp_username"],
                                        ftp_password=kwargs["ftp_password"],
                                        ftp_rootdir=kwargs["ftp_rootdir"])

    utils.delete_location_logs()
    return [u, p]


def send_email(msg, recipient, email, password):
    """
    Function for sending email using gmail.
    :param msg: Message
    :param recipient: Recipient email address.
    :param email: Sender email address.
    :param password: Sender password.
    :return: None
    """
    logger.info('')

    if recipient and email and password:
        email_sender.send_gmail(msg, args.recipient, args.email, args.password)
        print("Email sent!")
    return


if __name__ == '__main__':
    """
    Runs at execution from terminal.
    """
    print("News Globe initializing...")

    utils.create_articles_database()

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--debug", "-d",
        help="Logging level. One of [DEBUG,INFO,WARNING,ERROR,CRITICAL]. Default: CRITICAL",
        type=str, default="CRITICAL")

    parser.add_argument(
        "--articles", "-a",
        help="Number of articles to download. Default: All",
        type=int)
    DEFAULT_DAYS_TO_PARSE = -7
    parser.add_argument(
        '--range', '-r',
        help='Sets article parsing date range (today minus [integer] days). Default: %s' % DEFAULT_DAYS_TO_PARSE,
        type=int, default=DEFAULT_DAYS_TO_PARSE)

    parser.add_argument(
        '--interval', '-i',
        help='Enables periodic updates every [integer] seconds. Default=None',
        type=int, default=0)

    parser.add_argument(
        '--recipient',
        help='Sets auto-notification recipient.',
        type=str, default=None)
    parser.add_argument(
        '--email',
        help="Sets user's Gmail address.",
        type=str, default=None)
    parser.add_argument(
        '--password',
        help="Sets user's Gmail password.",
        type=str, default=None)

    parser.add_argument(
        '--ftp_host',
        help="Sets host FTP address",
        type=str, default=None)

    parser.add_argument(
        '--ftp_port',
        help="Sets host FTP port",
        type=int, default=21)

    parser.add_argument(
        '--ftp_username',
        help="Sets user's FTP username",
        type=str, default=None)

    parser.add_argument(
        '--ftp_password',
        help="Sets user's FTP password",
        type=str, default=None)

    parser.add_argument(
        '--ftp_rootdir',
        help="Sets host FTP root directory. (Into which static content will be copied...)",
        type=str, default="/")

    args = parser.parse_args()

    chosen_level = None

    if args.debug == "CRITICAL":
        chosen_level = logging.CRITICAL
    elif args.debug == "ERROR":
        chosen_level = logging.ERROR
    elif args.debug == "WARNING":
        chosen_level = logging.WARNING
    elif args.debug == "INFO":
        chosen_level = logging.INFO
    elif args.debug == "DEBUG":
        chosen_level = logging.DEBUG

    # noinspection PyUnboundLocalVariable
    logging.basicConfig(level=chosen_level, format=FORMAT)

    if args.interval == 0:
        print("Starting...")
        get_articles_range(
            args.range,
            args.articles,
            ftp_host=args.ftp_host,
            ftp_port=args.ftp_port,
            ftp_username=args.ftp_username,
            ftp_password=args.ftp_password,
            ftp_rootdir=args.ftp_rootdir)
        print("News Globe finished!")
    else:
        print("Starting periodic downloads every", args.interval, "seconds.")
        try:
            periodic_updater.schedule_periodic_function(
                get_articles_range,
                args.interval,
                args.range,
                args.articles,
                ftp_host=args.ftp_host,
                ftp_port=args.ftp_port,
                ftp_username=args.ftp_username,
                ftp_password=args.ftp_password,
                ftp_rootdir=args.ftp_rootdir)
            print("Done!")
        except Exception as e:
            time_str = datetime.datetime.strftime(
                datetime.datetime.now(), utils.TIME_FORMAT)
            message = """
            This is an automated message.

            Periodic updater stopped updating at %s.

            This is the error message:
            %s

            Have a nice day!
            """ % (time_str, e)
            send_email(message, args.recipient, args.email, args.password)
            raise
        except (KeyboardInterrupt, SystemExit):
            time_str = datetime.datetime.strftime(
                datetime.datetime.now(), utils.TIME_FORMAT)
            message = """
            This is an automated message.

            Periodic updater stopped updating at %s.

            It seems to be due to KeyboardInterrupt or SystemExit.

            Have a nice day!
            """ % time_str
            send_email(message, args.recipient, args.email, args.password)
            raise
