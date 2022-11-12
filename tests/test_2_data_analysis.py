import analyzer
import os
import sys
import logging

sys.path.append(os.path.abspath('.'))

# global variables
logger = None
analyzer.init_logger(logging.DEBUG)


def test_eps_1():
    """Analysis with pandas for EPS of 1.0.
    """
    files = analyzer.get_files_from_paths(['tests/files/eps/1eps.txt'])
    assert analyzer.parse_files_pandas(files, eps=True) == {
        'events': {
            'count': 3,
            'eps': 1.0
        }
    }


def test_eps_5():
    """Analysis with pandas for EPS of 5.0.
    """
    files = analyzer.get_files_from_paths(['tests/files/eps/5eps.txt'])
    assert analyzer.parse_files_pandas(files, eps=True) == {
        'events': {
            'count': 15,
            'eps': 5.0
        }
    }


def test_eps_5_w_gaps():
    """Analysis with pandas for complex EPS.
    """
    files = analyzer.get_files_from_paths(['tests/files/eps/5eps_gaps.txt'])
    assert analyzer.parse_files_pandas(files, eps=True) == {
        'events': {
            'count': 55,
            'eps': 0.16176470588235295
        }
    }


def test_mfip():
    """Analysis with pandas for the most frequent IP address.
    """
    files = analyzer.get_files_from_paths(['tests/files/eps/5eps.txt'])
    assert analyzer.parse_files_pandas(files, mfip=True) == {
        'mfip': {
            'ip_address': '10.10.10.5',
            'count': 11
        }
    }


def test_lfip():
    """Analysis with pandas for the lest frequent IP address.
    """
    files = analyzer.get_files_from_paths(['tests/files/eps/5eps.txt'])
    assert analyzer.parse_files_regex(files, lfip=True) == {
        'lfip': {
            'ip_address': '192.168.100.2',
            'count': 1
        }
    }


def test_bytes():
    """Analysis with pandas for the number of bytes transmitted.
    """
    files = analyzer.get_files_from_paths(['tests/files/eps/5eps.txt'])
    assert analyzer.parse_files_pandas(files, count_bytes=True) == {
        'bytes': {
            'body': 7480,
            'headers': 1520,
            'total': 9000
        }
    }


def test_all():
    """Full analysis with pandas.
    """
    files = analyzer.get_files_from_paths(['tests/files/eps/5eps_gaps.txt'])
    assert analyzer.parse_files_pandas(files, mfip=True, lfip=True, eps=True, count_bytes=True) == {
        'mfip': {
            'ip_address': '127.0.0.1',
            'count': 55
        },
        'lfip': {
            'ip_address': '127.0.0.1',
            'count': 55
        },
        'events': {
            'count': 55,
            'eps': 0.16176470588235295
        },
        'bytes': {
            'body': 331550,
            'headers': 299272,
            'total': 630822
        }
    }
