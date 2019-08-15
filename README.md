# News Globe
Latest news. On a globe. 

## About
The purpose of the program is to display world news on a 3D map. News is gathered through RSS feeds, and the GUI is made using HTML/CSS/JS and can be used via any modern browser.

The app back-end (Python) is periodically scraping RSS feeds from major news sites, and then analysing the data using Natural Language Processing (spaCy). This information is then passed on to the front-end HTML/CSS/JS application, which relies on an open-source library for 3D mapping (CesiumJS). It is refreshed every 15 minutes.

The main part of the program is made using the Python scripting language. At this point, a special thanks needs to be made to everyone in the Python community (especially StackOverflow) for all the tutorials, examples, one-liners etc., that helped me learn and write better code, and to the authors and contributors to the open-source libraries used in the creation of News Globe. This project would not work without these cool Python libraries:

- itsdangerous
- newspaper
- flask
- peewee
- requests
- tqdm
- peewee
- newspaper3k
- feedparser
- bs4
- simplejson
- flask-recaptcha
- spacy
- cherrypy
- paste
- pytest
- deepdiff

## Installation
1. Install Python
2. Install required packages using pip install -r requirements.txt
3. Download and install spacy English models using python -m spacy download en
4. Register with Cesium and add the Ion Access Token to static/news_globe.js

## Usage
1. For news gathering, run news_globe.py
2. Start local server (e.g. python -m http.server or using NodeJS or any other method)
3. Navigate to index.html. News will be visible once they are downloaded.

## TODO
- Documentation
- Optimization
- Computer Learning implementation of location search, themes search
- Non-HTML/JS/CSS GUI (PyQT/OpenGL)
- Bug fixes, improvements, suggestions

## Author and contact
Miha Smrekar
miha.smrekar9@gmail.com


