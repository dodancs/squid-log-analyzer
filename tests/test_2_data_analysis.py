import analyzer
import os
import sys
import logging

sys.path.append(os.path.abspath('.'))

# global variables
logger = None
analyzer.init_logger(logging.DEBUG)


def test_eps_1():
    files = analyzer.get_files_from_paths(['tests/files/eps/1eps.txt'])
    assert analyzer.parse_files(files, eps=True) == {
        'eps': {
            'count': 1.0
        }
    }


def test_eps_5():
    files = analyzer.get_files_from_paths(['tests/files/eps/5eps.txt'])
    assert analyzer.parse_files(files, eps=True) == {
        'eps': {
            'count': 5.0
        }
    }


def test_eps_5_w_gaps():
    files = analyzer.get_files_from_paths(['tests/files/eps/5eps_gaps.txt'])
    assert analyzer.parse_files(files, eps=True) == {
        'eps': {
            'count': 0.16176470588235295
        }
    }


def test_mfip():
    files = analyzer.get_files_from_paths(['tests/files/eps/5eps.txt'])
    assert analyzer.parse_files(files, mfip=True) == {
        'mfip': {
            'ip_address': '10.10.10.5',
            'count': 11
        }
    }


def test_lfip():
    files = analyzer.get_files_from_paths(['tests/files/eps/5eps.txt'])
    assert analyzer.parse_files(files, lfip=True) == {
        'lfip': {
            'ip_address': '192.168.100.2',
            'count': 1
        }
    }


def test_bytes():
    files = analyzer.get_files_from_paths(['tests/files/eps/5eps.txt'])
    assert analyzer.parse_files(files, count_bytes=True) == {
        'bytes': {
            'body': 7480,
            'headers': 1520,
            'total': 9000
        }
    }


def test_all():
    files = analyzer.get_files_from_paths(['tests/files/eps/5eps_gaps.txt'])
    assert analyzer.parse_files(files, mfip=True, lfip=True, eps=True, count_bytes=True) == {
        'mfip': {
            'ip_address': '127.0.0.1',
            'count': 55
        },
        'lfip': {
            'ip_address': '127.0.0.1',
            'count': 55
        },
        'eps': {
            'count': 0.16176470588235295
        },
        'bytes': {
            'body': 331550,
            'headers': 299272,
            'total': 630822
        }
    }
