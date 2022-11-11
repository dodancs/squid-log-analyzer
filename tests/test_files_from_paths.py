import importlib
import os
import regex

squid_log_analyzer = importlib.import_module("squid-log-analyzer")

def test_simple():
    out = squid_log_analyzer.get_files_from_paths(['tests/files/one/'])
    assert out == [os.path.abspath('tests/files/one/log.txt')]

def test_regex1():
    out = squid_log_analyzer.get_files_from_paths(['tests/files/regex'], recurse = False, pattern_filter = regex.compile('\.txt'))
    assert out == [os.path.abspath('tests/files/regex/log.txt.gz'), os.path.abspath('tests/files/regex/log.txt')]

def test_regex2():
    out = squid_log_analyzer.get_files_from_paths(['tests/files/regex'], recurse = False, pattern_filter = regex.compile('\.txt$'))
    assert out == [os.path.abspath('tests/files/regex/log.txt')]

def test_nested():
    out = squid_log_analyzer.get_files_from_paths(['tests/files/nested'], recurse = True)
    assert out == [os.path.abspath('tests/files/nested/first.txt'), os.path.abspath('tests/files/nested/other/last/last.txt')]
