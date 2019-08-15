import objects
import json

import utils


def database_date_cleanup():
    for a in objects.ArticleObject.select():
        json_t = json.loads(a.json)
        pub = json_t["publishedAt"]
        pub = utils.clean_datetime_string(pub)
        json_t["publishedAt"] = pub
        a.json = json.dumps(json_t)
        a.save()


def show_keywords():
    i = 0
    for a in objects.ArticleObject.select():
        j = json.loads(a.json)
        if "keywords" not in j:
            i += 1
            a.delete_instance()


def database_url_cleanup(url_str):
    for a in objects.ArticleObject.select():
        if url_str in a.url:
            print(a.url)
            a.delete_instance()


def database_delete_keywords():
    for a in objects.ArticleObject.select():
        j = json.loads(a.json)
        del j["keywords"]
        a.json = json.dumps(j)
        a.save()
