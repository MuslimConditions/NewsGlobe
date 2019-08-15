import pytest

import news_globe

if __name__ == "__main__":
    pytest.main([__file__, '-s', "-v"])


class downloader_mock:
    class Updater:
        def __init__(self):
            self.update_called = False
            self.save_to_database_called = False

        def update(self):
            self.update_called = True

        def save_to_database(self):
            self.save_to_database_called = True


class ParsingMock:
    class Parser:
        def __init__(self):
            self.parse_date_range_called = False
            self.parse_articles_called = False

        def parse_date_range(self):
            self.parse_date_range_called = True

        def parse_articles(self):
            self.parse_articles_called = True


def test_get_articles_range():
    u, p = news_globe.get_articles_range(None, None, downloader=downloader_mock, parsing=ParsingMock, test=True)
    assert u.update_called == True
    assert p.parse_date_range_called == True
