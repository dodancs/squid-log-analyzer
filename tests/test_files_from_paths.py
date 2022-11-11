import importlib
import os
import sys
import re

sys.path.append(os.path.abspath('..'))
main = importlib.import_module("main")

def test_simple():
    out = main.get_files_from_paths(['tests/files/one/'])
    assert out == [os.path.abspath('tests/files/one/log.txt')]

def test_regex1():
    out = main.get_files_from_paths(['tests/files/regex'], recurse = False, pattern_filter = re.compile('\.txt'))
    assert not set(out).difference({os.path.abspath('tests/files/regex/log.txt'), os.path.abspath('tests/files/regex/log.txt.gz')})

def test_regex2():
    out = main.get_files_from_paths(['tests/files/regex'], recurse = False, pattern_filter = re.compile('\.txt$'))
    assert out == [os.path.abspath('tests/files/regex/log.txt')]

def test_nested():
    out = main.get_files_from_paths(['tests/files/nested'], recurse = True)
    assert not set(out).difference({os.path.abspath('tests/files/nested/first.txt'), os.path.abspath('tests/files/nested/other/last/last.txt')})
