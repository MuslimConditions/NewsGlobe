import os

import peewee

FILE_PATH = os.path.dirname(os.path.realpath(__file__))
DATABASE_LOCATION = os.path.join(FILE_PATH, 'obj', 'articles.db')

db = peewee.SqliteDatabase(DATABASE_LOCATION)


class ArticleObject(peewee.Model):
    url = peewee.TextField(primary_key=True)
    json = peewee.TextField()

    class Meta:
        database = db
