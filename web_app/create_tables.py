from server import *
import datetime
from hashlib import md5

create_tables()

user = User.create(
    username="admin",
    password=md5("admin".encode('utf-8')).hexdigest(),
    email="",
    join_date=datetime.datetime.now(),
    admin=True,
    confirmed=True)
user.save()
