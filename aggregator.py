import re

import tqdm

import utils


def compare_articles(articles):
    # print(articles)
    thematics = []
    articles = list(articles)
    w = 0
    t = tqdm.tqdm(
        total=len(articles),
        bar_format="Aggregating |{bar}|{n_fmt}/{total_fmt} {percentage:3.0f}% {rate_fmt}")
    thematic_number = 0
    articles.sort(key=lambda x: len(x["keywords"]), reverse=True)
    if len(articles) > 0:
        print("First article from sorting has", len(articles[0]["keywords"]), "keywords.")
        print("Last article from sorting has", len(articles[-1]["keywords"]), "keywords.")
    while len(articles) > 0:
        t.update()
        w = w + 1
        d = articles.pop()
        url, kw = d["url"], d["keywords"]
        kw = filter_keywords(kw)
        if kw:
            if len(thematics) == 0:
                # No thematics, create first thematic
                thematic_number += 1
                thematics.append(
                    {"keywords": kw,
                     "thematic_number": thematic_number,
                     "articles": [{"dict": d, "matching": list(kw)}]})
            else:
                best = (0, set([]), set([]))
                for i in range(len(thematics)):
                    matching = set(thematics[i]["keywords"].keys()) & set(kw.keys())

                    if len(matching) > len(best[1]):
                        best = (i, list(matching), list(kw.keys()))

                best_thematic = thematics[best[0]]
                number_of_keywords = len(best[2])
                if number_of_keywords == 0:
                    number_of_keywords = 1e100
                if len(best[1]) / number_of_keywords > 0.33:
                    best_thematic["articles"].append({"dict": d, "matching": best[1]})
                    if w % 1000 == 0:
                        thematics.sort(key=lambda x: len(x["articles"]), reverse=True)
                else:
                    # create new thematic
                    thematic_number += 1
                    thematics.append(
                        {"keywords": kw, "thematic_number": thematic_number,
                         "articles": [{"dict": d, "matching": list(kw)}]})
        else:
            # print("No keywords after filtering")
            # No keywords after filtering
            thematic_number += 1
            thematics.append(
                {"keywords": kw, "thematic_number": thematic_number, "articles": [{"dict": d, "matching": list(kw)}]})
    t.close()
    print("Aggregated %s articles into thematics" % w)
    i = 0
    for t in thematics:
        for _ in t['articles']:
            i += 1
    if i != w:
        raise Exception("Number of input articles != number of output articles")
    # print(thematics)
    return thematics


def filter_keywords(kw_dict, max_words=2, min_words=1):
    out = {}
    items = sorted(kw_dict.items(), key=lambda x: x[1], reverse=True)[:15]
    for keyword, occurrences in items:
        keyword = utils.clean_string(keyword)
        if max_words >= len(keyword.split()) >= min_words:
            if len(keyword) > 2:
                if is_word_checked(keyword):
                    out[keyword] = occurrences

    if len(out) > 0:
        return out
    else:
        return None


def is_word_checked(string):
    avoid = ["getty",
             "new york times",
             "http",
             "www",
             "continue reading",
             "people",
             "year",
             "reuters",
             "world",
             "subscrib",
             "bloomberg",
             "cnn",
             "news",
             "full",
             "article",
             "rtcom",
             "read",
             "welle",
             "deutsche",
             "germany",
             "hong",
             "times",
             "kong"]
    for a in avoid:
        if a in string:
            return False
    if has_numbers(string):
        return False
    return True


def has_numbers(inputString):
    return bool(re.search(r'\d', inputString))
