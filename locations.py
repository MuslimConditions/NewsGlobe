import json
import logging
import os
import re

import spacy
import tqdm

import utils

logger = logging.getLogger(__name__)
FILE_PATH = os.path.dirname(os.path.realpath(__file__))


# avoid = set(json.load(open(os.path.join(FILE_PATH,"obj","avoid_locations.json"),'r')))

# avoid = [a.lower() for a in avoid]

# print("Loading locations")
#

def combine(lst, num):
    logger.info('')
    """
    Takes in a list
    [1,2,3,4,5]
    and based on the num returns all possible neighbouring pairs
    [[1,2],[2,3],[3,4],[4,5]].
    :param lst: input list
    :param num: number of neighbouring pairs
    :return: list.
    """
    if len(lst) < num:
        raise Exception("Cannot have more neighbours than length of list.")
    out = []
    for i in range(len(lst) - num + 1):
        out.append(lst[i:i + num])
    return out


def string_combinations(string, max_words):
    logger.info('')
    """
    Takes a string text and creates a list of all possible neighbouring strings.
    :param string: Input string
    :param max_words: Number of neighbouring strings
    :return: list
    """
    if max_words == 0:
        return None
    s = re.findall(r"[\w']+", string)
    r = combine(s, max_words)
    return [utils.clean_string(' '.join(a)) for a in r]


def all_combinations(string, max_words):
    logger.info('')
    """
    Creates list of i=1, i=2, i=3, to i=max_words combinations of words in string.
    :param string: String text
    :param max_words: Integer number of max neighbouring words.
    :return: List of all combinations.
    """
    out = []
    i = 0
    while i < max_words:
        i += 1
        out = out + string_combinations(string, i)
    return out


def all_stopwords():
    logger.info('')
    """
    Gets stopwords from json file.
    :return: set of stopwords
    """
    sws = json.loads(open(os.path.join(FILE_PATH, "obj", 'stopwords-all.json'), 'rb').read())
    out = [sws[a] for a in sws]
    sws = []
    for l in out:
        sws += l
    sws = set(sws)
    return sws


def all_english_words():
    logger.info('')
    words = [w.split(',')[0].replace('"', '').lower()
             for w in open(os.path.join(FILE_PATH, "obj", 'dictionary.csv'), 'r').readlines()]
    return set(words)


# noinspection PyShadowingNames
def all_surnames():
    logger.info('')
    surnames = [w.split(',')[0].lower()
                for w in open(os.path.join(FILE_PATH, "obj", 'surnames.csv'), 'r').readlines()]
    return set(surnames)


# noinspection PyShadowingNames
def all_firstnames():
    logger.info('')
    firstnames = [w.split(',')[0].lower()
                  for w in open(os.path.join(FILE_PATH, "obj", 'first_names.csv'), 'r').readlines()]
    return set(firstnames)


# english_words = all_english_words()
# stopwords = all_stopwords()
# surnames = all_surnames()
# firstnames = all_firstnames()

class LocationLoader:
    """
    Geoextraction class that loads location data from files and puts them into RAM.
    """

    def __init__(self):
        logger.info('')
        self.lookup_id = 0
        self.locations, self.locations_lookup, self.countries_cca2 = self.load_locations()
        self.locations_lookup_set = set(self.locations_lookup.keys())

    def load_locations(self):
        logger.info('')
        """
        Function that loads countries, cities and states from files and returns two dictionaries:
            First dictionary:
                -keys are lookup ids
                -values are location data (common name, latitude, longtitude, population, type [country, city, state])
            Second dictionary:
                -keys are all different location names (UK, United Kingdom, England, f.e.)
                -values are lookup ids

        This enables fast checking if a random word is in fact a location (using common set elements),
        and in-turn fast lookup using the lookup id.
        :return:
        """
        print("Loading locations...")
        countries, countries_lookup, countries_cca2 = self.load_countries()
        # print()
        cities, cities_lookup = self.load_cities()
        states, states_lookup = self.load_states()
        location_dict = {**cities, **states, **countries}
        lookup_dict = {**cities_lookup, **states_lookup, **countries_lookup}
        lookup_dict = {k.lower(): v for k, v in lookup_dict.items()}

        del (lookup_dict[""])  # TODO: Fix this (better parsing)
        print("...Done!")

        return location_dict, lookup_dict, countries_cca2

    def load_countries(self):
        logger.info('')
        """
        Loads countries from file and generates two dictionaries.
        First dictionary:
            -keys are lookup ids
            -values are location data
        Second dictionary:
            -keys are all different location names
            -values are lookup ids
        :return: dict, dict
        """
        countries = {}
        countries_lookup = {}
        countries_cca2 = {}
        f = open(os.path.join(FILE_PATH, 'obj', 'countries.json'), 'r', encoding='utf-8').read()
        j = json.loads(f)
        for c in j:
            self.lookup_id += 1
            if len(c['latlng']) > 0:
                lat, lng, cca2, cca3 = c['latlng'][0], c['latlng'][1], c['cca2'], c['cca3']
                countries[self.lookup_id] = {'location': c['name']['common'], 'lat': lat, 'lng': lng,
                                             'type': 'country', 'area': c['area']}
                # print(c['name']['common'])
                for k, v in c['name'].items():
                    if isinstance(v, dict):
                        for k1, v1 in v.items():
                            for k2, v2 in v1.items():
                                countries_lookup[v2] = self.lookup_id
                    else:
                        # print("   "+v)
                        countries_lookup[v] = self.lookup_id
                for n in c['altSpellings']:
                    countries_lookup[n] = self.lookup_id

                countries_cca2[cca2] = self.lookup_id
            # else:
            #    logger.warning("country "+c['name']['common']+' has no latlng')
        return countries, countries_lookup, countries_cca2

    def load_cities(self, min_population=0):
        logger.info('')
        """
        Loads cities from file and generates two dictionaries.
        First dictionary:
            -keys are lookup ids
            -values are location data
        Second dictionary:
            -keys are all different location names
            -values are lookup ids
        :return: dict, dict
        """
        f = open(os.path.join(FILE_PATH, 'obj', 'cities1000.txt'), 'r', encoding='utf-8')
        cities = {}
        cities_lookup = {}
        for l in f.readlines():
            split = l.split(';')
            go = False
            population, lat, lng, ascii_name, alternate_names, admin_region, name, country_code = None, None, None, None, None, None, None, None
            if len(split) == 19:
                idn, name, ascii_name, alternate_names, lat, lng, feat_class, feat_code, \
                country_code, a1, a2, a3, a4, a5, population, dem, elevation, admin_region, mod_date = split
                go = True
            elif len(split) == 17:
                idn, name, ascii_name, alternate_names, lat, lng, feat_class, feat_code, \
                country_code, a1, a2, a3, population, dem, elevation, admin_region, mod_date = split
                go = True
            if go:
                admin_region_splitted = admin_region.split("/")
                state = None
                county = None
                continent = None
                if len(admin_region_splitted) == 2:
                    continent, county = admin_region_splitted
                elif len(admin_region_splitted) == 3:
                    continent, state, county = admin_region_splitted
                self.lookup_id += 1
                population = int(population)
                if population >= min_population:
                    lat = float(lat)
                    lng = float(lng)

                    cities[self.lookup_id] = {'location': name,
                                              'lat': lat,
                                              'lng': lng,
                                              'population': population,
                                              'type': 'city',
                                              'country': country_code,
                                              'continent': continent,
                                              "county": county}
                    if state:
                        cities[self.lookup_id]['state'] = state

                    all_possible_names = [name, ascii_name] + [n for n in alternate_names.split(',')]
                    for n in all_possible_names:
                        if n not in cities_lookup:
                            cities_lookup[n] = self.lookup_id
                        if population > cities[cities_lookup[n]]['population']:
                            cities_lookup[n] = self.lookup_id

        return cities, cities_lookup

    def load_states(self):
        logger.info('')
        """
        Loads states from file and generates two dictionaries.
        First dictionary:
            -keys are lookup ids
            -values are location data
        Second dictionary:
            -keys are all different location names
            -values are lookup ids
        :return: dict, dict
        """
        f = open(os.path.join(FILE_PATH, "obj", "states.json"), 'r')
        j = json.loads(f.read())
        states = {}
        states_lookup = {}
        for i in range(len(j)):
            self.lookup_id += 1
            states[self.lookup_id] = {'location': j[i]['state'], 'lat': j[i]['latitude'], 'lng': j[i]['longitude'],
                                      'type': 'state', "country": "US"}
            states_lookup[j[i]['state']] = self.lookup_id
        return states, states_lookup

    def get_lookup_id(self, string):
        if string.lower() in self.locations_lookup:
            ids = self.locations_lookup[string.lower()]
            logger.debug(string + '-->' + str(ids))
            return ids
        return None

    def get_location_from_id(self, str_id):

        if str_id in self.locations:
            out = self.locations[str_id]
            # print(out)
            logger.debug(
                str(str_id) + '-->' + out['location'] + '(lat:' + str(out['lat']) + ',lng:' + str(out['lng']) + ')')
            return out
        return None

    def get_location(self, string):
        logger.debug('')
        lookup_id = self.get_lookup_id(string)
        if lookup_id:
            loc = self.get_location_from_id(lookup_id)
            if loc:
                return loc
        return None


def get_locations(article_list, location_loader, nlp):
    logger.info('')
    """
    Takes in a string and outputs list of locations that are present in string.
    :param logger_internal:
    :param location_loader:
    :param string: String to be parsed.
    :return: list of a single dictionary per location
    """

    t = tqdm.tqdm(
        total=len(article_list),
        bar_format="Spacy processing |{bar}|{n_fmt}/{total_fmt} {percentage:3.0f}% {rate_fmt}")

    for a in article_list:

        string = a['title']
        if "description" in a:
            string += ". " + a["description"]
        doc = nlp(string)
        matches = [ent.text for ent in doc.ents if ent.label_ == "LOC" or ent.label_ == "GPE"]
        occuring_ids = {}
        for name in matches:
            count = string.count(name)
            lookup_id = location_loader.get_lookup_id(name)
            if lookup_id != None:
                if lookup_id in occuring_ids:
                    occuring_ids[lookup_id] += count
                else:
                    occuring_ids[lookup_id] = count
        out = []
        for occurring_id, count in occuring_ids.items():
            d = location_loader.get_location_from_id(occurring_id)
            d['count'] = count
            out.append(d)
        out.sort(key=lambda x: x['count'], reverse=True)
        # logstring= '\n'+string+'\n'+str(matches)+'\n'+str([l for l in out])
        # logstring = logstring.encode().decode("ascii",'replace')
        # logger_internal.info(logstring)
        a['locations'] = out
        t.update()
    t.close()
    return article_list


def string_found(substring, string):
    logger.info('')
    """Returns True if substring word is found within a string sentence
    (has to be surrounded by whitespace).
    
    
    Arguments:
        substring {str} -- word
        string {str} -- sentence
    
    Returns:
        bool -- True or False
    """
    if re.search(r"\b" + re.escape(substring) + r"\b", string):
        return True
    return False


def geocode_results(articles,location_loader=None):
    logger.info('')
    """
    Function that takes a list of article dictionaries,
    and returns the same list with updated article dictionaries, that now include geo data.
    :param articles: list of dicts
    :return: list of dicts (geocoded)
    """

    # log_path = os.path.join(FILE_PATH,'logs','locations','%s.log' % utils.date_to_string(datetime.datetime.now(),'%Y-%m-%dT%H-%M-%SZ'))
    # fh = logging.FileHandler(log_path,'w','utf-8')
    # old_handlers = logger.handlers
    # logger.handlers = []
    # logger.addHandler(fh)
    # logger.propagate = False
    if not location_loader:
        logger.warning('Loading location loader from within this function, is unoptimised behaviour.')
        location_loader = LocationLoader()
    nlp = spacy.load('en', disable=['parser', 'tagger', 'textcat', 'tokenizer'])
    articles_tagged = get_locations(articles, location_loader, nlp)
    return articles_tagged


def geocode_string(string):
    logger.info('')
    # locations,locations_lookup,locations_lookup_set,countries_cca2 = load_locations_dicts()
    location_loader = LocationLoader()
    nlp = spacy.load('en', disable=['parser', 'tagger', 'textcat', 'tokenizer'])
    return get_locations([{'title': string}], location_loader, nlp)

# print(geocode_string('Tunisia'))
