import simplejson as json
import logging
import os
from collections import Counter

import tqdm

import aggregator
import locations
import utils
import gzip

logger = logging.getLogger(__name__)

FILE_PATH = os.path.dirname(os.path.realpath(__file__))
DEFAULT_BAR_FORMAT = " |{bar}|{n_fmt}/{total_fmt} {percentage:3.0f}% {rate_fmt}"


class Parser:
    """
    Class that is used to fetch articles from the local articles database,
    geocode the articles,
    categorise them,
    and write a JSON file with location-tagged articles.
    """

    def __init__(self):
        """
        Initialisation includes:
        -setting the local class variables
        -loading stopwords
        -loading locations using LocationLoader
        """
        logger.info('')
        self.counted_by_location = {}
        self.out_articles = None
        self.out_thematics = None
        self.stopwords = json.loads(open(os.path.join(FILE_PATH, "obj", 'stopwords-all.json'), 'rb').read())
        self.location_loader = locations.LocationLoader()

    def print_articles(self):
        """
        Function that prints articles using a nice format for debugging purposes.
        :return: None
        """
        logger.info('')
        for a in self.out_articles:
            print('-----')
            print(a['title'], a['url'].split('//')[1].split('/')[0])
            print('')
            print(a['text'])

    def get_keywords(self, txt, url, language='en'):
        """
        Function that gets a text, and returns a dictionary of keywords.

        It does this by removing the stopwords in the text and then counting the words.
        :param txt: String of text, that we want to get keywords to.
        :param url: Url from which text was fetched.
        :return:
        """
        logger.info(url + ':' + txt)
        outs = []
        swords = set(self.stopwords[language])
        for w in txt.split():
            w = utils.clean_string(w).lower()
            if w not in swords and len(w) > 1:
                outs.append(w)
        out = Counter(outs).most_common()
        d = {}
        for w, o in out:
            d[w] = o
        return d

    def get_thematics(self):
        """
        Function that takes self.out_articles and aggregates them to thematics using aggregator.
        It then rewrites self.out_articles with thematic numbers appended to each article,
        and adds a self.out_thematics variable that holds information about each thematic and related articles.
        :return: None
        """
        logger.info('')
        out_articles = []
        print("Aggregating %s articles into thematics..." % len(self.out_articles))
        thematics = aggregator.compare_articles(self.out_articles)
        thematics.sort(key=lambda x: len(x["articles"]))

        for t in thematics:
            for a in t['articles']:
                a['dict']['thematic_number'] = t['thematic_number']
                out_articles.append(a['dict'])

        self.out_thematics = thematics
        self.out_articles = out_articles

    @staticmethod
    def filter_article_dict(value_dictionary):
        """
        Function that takes as the input an article dictionary, and returns the same dictionary,
            with all unneccessary keys removed.
        :param value_dictionary: Article dictionary.
        :return: Article dictionary (filtered).
        """
        logger.info('')

        lat = value_dictionary["lat"]
        lng = value_dictionary["lng"]
        url = value_dictionary["url"]
        location = value_dictionary["location"]
        published_at = value_dictionary["publishedAt"]
        title = value_dictionary["title"]
        thematic_number = value_dictionary['thematic_number']

        value = {"title": title,
                 "url": url,
                 "location": location,
                 "publishedAt": published_at,
                 "lat": lat,
                 "lng": lng,
                 'thematic_number': thematic_number}
        return value

    def parse_articles(self, articles):
        """
        Main function of the Parser class.

        Input is a list of articles, that are NOT YET geocoded or sorted into thematics and without keywords.

        The function then:
        -creates an empty self.out_articles list,
        -gets keywords for the articles,
        -geocodes the articles,
        -chooses the best location for each article using parse_article_object to be used,
        -appends each geocoded article article to self.out_articles,
        -generates thematics from the keywords
        -counts articles by locations

        The resulting organised articles are finally written into a JSON file.

        :param articles: List of dictionaries with article data.
        :return:
        """
        logger.info('')

        # Creating an empty self.out_articles list
        self.out_articles = []

        # Getting keywords
        print("Parsing %s articles..." % len(articles))
        print("Appending keywords...")
        for a in articles:
            a['keywords'] = self.get_keywords(txt=a['title'] + ". " + a['description'], url=a['url'])

        # Geocoding
        articles = locations.geocode_results(articles, location_loader=self.location_loader)

        # Choosing best location
        t = tqdm.tqdm(total=len(articles),bar_format="Parsing |{bar}|{n_fmt}/{total_fmt} {percentage:3.0f}% {rate_fmt}")
        for a in articles:
            t.update()
            r = self.parse_article_object(a)
            if r:
                # Appending to self.out_articles
                self.out_articles.append(r)
        t.close()

        # Generating thematics
        self.get_thematics()

        # Counting by location
        self.generate_counted_by_location()

        # Writing to JSON
        self.write_counted_2_json()

    def parse_date_range(self, limit=None, date_from_str=None, date_to_str=None, timedelta=0):
        """
        This function gets articles based on the time of creation from the database,
        and calls self.parse_articles() on the fetched articles.

        :param limit: Maximum number of articles.
        :param date_from_str: Minimum date string.
        :param date_to_str: Maximum date string.
        :param timedelta: Integer : number of days to add.
        :return: None
        """

        logger.info('')

        self.out_articles = []

        date_from = utils.parse_date_str(date_from_str, timedelta)  # timedelta
        date_to = utils.parse_date_str(date_to_str, 1)  # next midnight

        print("Parsing date range %s to %s..." % (utils.date_to_string(date_from), utils.date_to_string(date_to)))

        articles = utils.get_article_daterange(date_from, date_to)
        articles = articles[:limit]

        self.parse_articles(articles)

    # noinspection PyUnusedLocal
    def parse_article_object(self, obj):
        """
        Function that receives an article object (which is already geocoded), and returns the same object,
        with lat, lng and location keys added.

        It selects the probable location of article using a manual rule-based logic.

        :param obj:
        :return:
        """
        logger.info(obj['title'])
        r = obj

        title = r["title"]
        text = r["description"]
        lctns = r['locations']

        if text is None:
            text = ""

        # final location
        _location = None

        # only proceed if there are any locations to choose from
        if len(lctns) > 0:

            # if the first location (most frequently mentioned ?) is a city, it is of good enough accuracy.
            if lctns[0]['type'] == "city":
                _location = lctns[0]

            # if the first location is a state, try to check if there is another location within that state,
            #     which could improve the location accuracy.
            else:
                # create list for all better options
                better_options = []

                # if the first location is a state or county, check if any cities are in that state or county.
                if lctns[0]['type'] == "state":
                    for candidate in lctns[1:]:
                        if candidate['type'] == "city":
                            first_location_id = self.location_loader.get_lookup_id(lctns[0]['location'])
                            if "state" in candidate:
                                candidate_state_id = self.location_loader.get_lookup_id(candidate["state"])
                                if candidate_state_id == first_location_id:
                                    better_options.append(candidate)
                            if "county" in candidate:
                                candidate_county_id = self.location_loader.get_lookup_id(candidate["county"])
                                if candidate_county_id == first_location_id:
                                    better_options.append(candidate)

                # if the first location is a country, check if any cities are in that county
                # TODO: check if any states are in that county.
                if lctns[0]['type'] == "country":
                    for candidate in lctns[1:]:
                        if candidate['type'] == "city":
                            candidate_country_id = self.location_loader.get_lookup_id(candidate["country"])
                            first_location_id = self.location_loader.get_lookup_id(lctns[0]['location'])
                            if candidate_country_id == first_location_id:
                                better_options.append(candidate)

                if len(better_options) > 0:
                    _location = better_options[0]
                else:
                    _location = lctns[0]

            loc, lat, lng = _location['location'], _location['lat'], _location['lng']
            r["lat"] = lat
            r["lng"] = lng
            r["location"] = loc
            return r

    def parse_url(self, url):
        logger.info('')
        article = utils.get_article_from_database(url)
        r = self.parse_article_object(article)
        if r:
            self.filter_article_dict(r)
            self.out_articles.append(r)

    def generate_counted_by_location(self):
        logger.info('')
        for a in self.out_articles:
            coords = '%0.5f,%0.5f' % (a['lat'], a['lng'])
            if coords in self.counted_by_location:
                self.counted_by_location[coords]["count"] += 1
                self.counted_by_location[coords]['articles'].append({
                    'title': a["title"],
                    'url': a["url"],
                    'publishedAt': a['publishedAt'],
                    'thematic_number': a["thematic_number"]
                })
            else:
                self.counted_by_location[coords] = {
                    "count": 1,
                    "lat": "%0.5f" % a["lat"],
                    "lng": "%0.5f" % a["lng"],
                    "articles": [{
                        'title': a["title"],
                        'url': a["url"],
                        'publishedAt': a['publishedAt'],
                        'thematic_number': a["thematic_number"]
                    }],
                    'location': a["location"]
                }
        return self.counted_by_location

    def write_2_json(self):
        logger.info('')
        out_json = []
        print("Preparing JSON output file...")
        for a in self.out_articles:
            out_json.append(self.filter_article_dict(a))
        print("Writing to JSON, dumping %s articles..." % len(out_json))
        json_file_path = os.path.join(FILE_PATH, 'static', 'markers.json')
        with open(json_file_path, 'w') as outfile:
            json.dump(out_json, outfile)

    def write_thematics_2_json(self):
        logger.info('')
        print("Writing thematics to JSON, dumping %s thematics..." % len(self.out_thematics))
        json_file_path = os.path.join(FILE_PATH, 'static', 'thematics.json')
        with open(json_file_path, 'w') as outfile:
            json.dump(self.out_thematics, outfile)

    def write_counted_2_json(self):
        logger.info('')
        print("Writing counted to JSON, dumping %s locations..." % len(self.counted_by_location))
        json_file_path = os.path.join(FILE_PATH, 'static', 'counted_by_location')
        with gzip.open(json_file_path, 'wb') as outfile:
            outfile.write(json.dumps(self.counted_by_location).encode('utf-8'))
