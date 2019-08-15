#!/usr/bin/env python
# -*- coding: utf-8 -*-

import aggregator


def test_has_numbers():
    assert aggregator.has_numbers("1234") == True
    assert aggregator.has_numbers("asdf") == False
    assert aggregator.has_numbers("a1s2") == True


def test_is_word_checked():
    assert aggregator.is_word_checked("somegettytest") == False
    assert aggregator.is_word_checked("test") == True
    assert aggregator.is_word_checked("12test") == False
