import os
import sys
import re
import logging

sys.path.append(os.path.abspath('.'))
import analyzer

# global variables
logger = None
analyzer.init_logger(logging.DEBUG)

def test_simple():
    """Test for finding one log file within a directory
    """
    out = analyzer.get_files_from_paths(['tests/files/one/'])
    assert out == [os.path.abspath('tests/files/one/log.txt')]

def test_regex1():
    """Test for verifying that simple RegEx patterns work correctly.
    """
    out = analyzer.get_files_from_paths(['tests/files/regex'], recurse = False, pattern_filter = re.compile(r'\.txt'))
    assert not set(out).difference({os.path.abspath('tests/files/regex/log.txt'), os.path.abspath('tests/files/regex/log.txt.gz')})

def test_regex2():
    """Test for verifying that strict RegEx patterns work correctly.
    """
    out = analyzer.get_files_from_paths(['tests/files/regex'], recurse = False, pattern_filter = re.compile(r'\.txt$'))
    assert out == [os.path.abspath('tests/files/regex/log.txt')]

def test_nested():
    """Test for finding nested log files within multiple directories.
    """
    out = analyzer.get_files_from_paths(['tests/files/nested'], recurse = True)
    assert not set(out).difference({os.path.abspath('tests/files/nested/first.txt'), os.path.abspath('tests/files/nested/other/last/last.txt')})
