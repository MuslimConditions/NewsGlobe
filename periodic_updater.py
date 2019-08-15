#!/bin/python
import logging
import time

logger = logging.getLogger(__name__)


def countdown(t):
    while t:
        mins, secs = divmod(t, 60)
        timeformat = '{:02d}:{:02d}'.format(mins, secs)
        print(timeformat, end='\r')
        time.sleep(1)
        t -= 1
    print("")


def schedule_periodic_function(func, period=30, *args, **kwargs):
    while True:
        func(*args, **kwargs)
        countdown(period)
