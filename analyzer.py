#! /usr/bin/env python3

import logging
import argparse
import os
import sys
import re
from pathlib import Path
import datetime
import pandas
import json


# global variables
logger = None


# get files to process from a list of paths
def get_files_from_paths(paths, recurse = False, pattern_filter = re.compile('.*')):
    global logger
    to_process = []

    # go through all input paths
    for p in paths:

        # if path is a regular file, add it
        if os.path.isfile(p):
            absolute_path = os.path.abspath(p)

            # if a path does not match pattern, skip it
            if not pattern_filter.search(absolute_path):
                logger.debug(f'Pattern \'{pattern_filter.pattern}\' does not match \'{absolute_path}\'.')
                continue

            # add file if not already added
            if absolute_path not in to_process:
                logger.debug(f'Adding file \'{p}\'.')
                to_process.append(absolute_path)

        # if path is a directory, search through it
        elif os.path.isdir(p):

            # go through paths in directory
            for pp in os.listdir(p):
                subpath = os.path.join(p, pp)

                # process files
                if os.path.isfile(subpath) and subpath not in paths:
                    paths.append(subpath)

                # process directories
                elif os.path.isdir(subpath):

                    # skip directory if recursion not allowed
                    if not recurse:
                        logger.debug(f'Skipping subdirectory \'{subpath}\'.')
                        continue

                    # also process files in subdirectory recursively
                    if subpath not in paths:
                        paths.append(subpath)

        # if path does not exist, show error
        else:
            logger.debug(f'Unable to access path \'{p}\'!')
            continue

    return to_process


def init_argparser():
    parser = argparse.ArgumentParser(description='Squid log analyzer.')

    parser.add_argument('input_paths', metavar='INPUT', type=str, nargs='+',
                        help='path to log files or a directory containing files')
    parser.add_argument('output_file', metavar='OUTPUT', type=str,
                        help='path to a JSON output file')

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='show verbose log output')
    parser.add_argument('--filter', action='append', type=str,
                        help='filter input files based on regex patterns')
    parser.add_argument('-r', '--recurse', action='store_true',
                        help='recursively search for files in sub-directories')
    parser.add_argument('-f', '--force', action='store_true',
                        help='overwrite output file if already exists')
    parser.add_argument('--fast', action='store_true',
                        help='use a fast regex-based analysis')

    operations = parser.add_argument_group('operations')
    operations.add_argument('--mfip', action='store_true',
                            help='analyze the most frequent IP address present')
    operations.add_argument('--lfip', action='store_true',
                            help='analyze the least frequent IP address present')
    operations.add_argument('--eps', action='store_true',
                            help='analyze the number of events per second')
    operations.add_argument('--bytes', action='store_true',
                            help='analyze the total number of bytes exchanged')

    parser.add_argument('--exclude-header-sizes', action='store_true',
                        help='exclude HTTP header sizes from the number of bytes exchanged')

    return parser


def init_logger(level):
    global logger

    logger = logging.getLogger()
    logger.setLevel(level)
    logger_handler = logging.StreamHandler(sys.stdout)
    logger_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(logger_handler)


# parse and analyze files with pandas
def parse_files_pandas(to_process, mfip = False, lfip = False, eps = False, count_bytes = False, exclude_header_sizes = False):
    all_data = pandas.DataFrame()
    result = {}

    # add all data into one dataframe
    for f in to_process:
        # read data from log file
        data = pandas.read_csv(f, delimiter=r'\s+', usecols=range(10), names=['Timestamp', 'Headers size', 'Source IP address', 'Response code', 'Body size', 'Request method', 'URL', 'Username', 'Destination IP address', 'Mimetype'], skip_blank_lines=True)
        all_data = pandas.concat([all_data, data])

    # if no data has been read - exit
    if not len(all_data):
        logger.info('Nothing to do - no data supplied.')
        sys.exit(0)

    # count the number of bytes transmitted
    if count_bytes:
        headers = 0

        # get all body sizes
        bodies = all_data[all_data['Body size'] > 0]['Body size'].sum()

        result['bytes'] = {
            'body': int(bodies)
        }

        # get all header sizes
        if not exclude_header_sizes:
            headers = all_data[all_data['Headers size'] > 0]['Headers size'].sum()
            result['bytes']['headers'] = int(headers)

        result['bytes']['total'] = int(bodies + headers)

    # count the occurence of source IP addresses
    if mfip or lfip:
        counts = all_data['Source IP address'].value_counts()

        # most frequent IP
        if mfip:
            result['mfip'] = {
                'ip_address': counts.head(1).index[0],
                'count': int(counts.head(1).values[0])
            }

        # least frequent IP
        if lfip:
            result['lfip'] = {
                'ip_address': counts.tail(1).index[0],
                'count': int(counts.tail(1).values[0])
            }

    # count the number of events every second and get the average
    if eps:
        all_data['Timestamp'] = pandas.to_datetime(all_data.Timestamp, unit='s')
        events = all_data.groupby(pandas.Grouper(key='Timestamp', freq='S'))['Timestamp'].count()

        result['events'] = {
            'count': len(all_data.values),
            'eps': sum(events.values) / len(events.values)
        }

    return result


# parse and analyze files with regex
def parse_files_regex(to_process, mfip = False, lfip = False, eps = False, count_bytes = False, exclude_header_sizes = False):
    result = {}

    ip_frequencies = {}

    event_num = 0
    epoch_start = None
    epoch_end = 0

    # too slow regex
    #regex_timestmap = r'(\d+.?\d+?)'
    #regex_ip = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    #regex_http_method = r'(CONNECT|HEAD|OPTIONS|GET|POST|PUT|DELETE|PATCH|TRACE)'
    #regex_url = r'(((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*)'
    # regex = re.compile(r'^' + regex_timestmap + r'\s+(\-?\d+)\s+' + regex_ip + r'\s+([A-Z0-9_/]+)\s+\-?(\d+)\s+' + regex_http_method + r'\s+' + regex_url + r'\s+([a-zA-Z\-_]+)\s+(([A-Z_/]+)' + regex_ip + r')\s+([a-z\-/]+)$')
    
    # the regex below this comment should be used, but it does not process a row that has more than 10 fields
    # https://www.secrepo.com/squid/access.log.gz on line 82948 has two log events merged into one line
    # and that yields different results, because without the --fast option, it also processes that line
    # regex = re.compile(r'^(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)$')

    # simpler regex is much faster
    regex = re.compile(r'^(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+).*')

    # prepare result byte count
    if count_bytes:
        result['bytes'] = {'body': 0}
        if not exclude_header_sizes:
            result['bytes']['headers'] = 0

    # process all
    for f in to_process:
        # read data from log file
        with open(f, 'r') as ff:
            # go through all lines
            for line in ff.readlines():
                # try to match regex pattern
                match = regex.search(line)

                # if the line does not match, skip it
                if not match:
                    continue

                # count events
                event_num += 1

                if eps:
                    # keep the epoch time start and end of all events
                    epoch = int(match.groups()[0].split('.')[0])
                    if not epoch_start or epoch_start > epoch:
                        epoch_start = epoch
                    if epoch > epoch_end:
                        epoch_end = epoch

                # count the frequency for IPs
                if mfip or lfip:
                    if not match.groups()[2] in ip_frequencies:
                        ip_frequencies[match.groups()[2]] = 1
                    else:
                        ip_frequencies[match.groups()[2]] += 1

                # add bytes from header and body
                if count_bytes:
                    body = int(match.groups()[4])
                    headers = int(match.groups()[1])

                    # sometimes the value can be -1
                    result['bytes']['body'] += body if body > 0 else 0

                    if not exclude_header_sizes:
                        # sometimes the value can be -1
                        result['bytes']['headers'] += headers if headers > 0 else 0

    # count the total number of bytes
    if count_bytes:
        result['bytes']['total'] = result['bytes']['body'] + result['bytes']['headers']

    # sort IP frequencies
    if mfip or lfip:
        ip_frequencies = sorted(ip_frequencies.items(), key=lambda x: x[1])
        ip_frequencies_len = len(ip_frequencies)

    # add the most frequent IP to the result
    if mfip:
        result['mfip'] = {
            'ip_address': ip_frequencies[ip_frequencies_len - 1][0],
            'count': ip_frequencies[ip_frequencies_len - 1][1]
        }

    # add the least frequent IP to the result
    if lfip:
        result['lfip'] = {
            'ip_address': ip_frequencies[0][0],
            'count': ip_frequencies[0][1]
        }

    # add the number of events per second to the result
    if eps:
        result['events'] = {
            'count': event_num,
            'eps': event_num / (epoch_end - epoch_start + 1)
        }

    return result


def run():

    # initialize argument parser
    parser = init_argparser()
    # parse arguments
    args = parser.parse_args()

    # set up logging
    init_logger(logging.DEBUG if args.verbose else logging.INFO)

    # check if at least one operation was set
    if not args.mfip and not args.lfip and not args.eps and not args.bytes:
        logger.info('Nothing to do - no operation supplied.')
        sys.exit(0)

    # prepare pattern filters
    filters = '.*'
    if args.filter:
        filters = '|'.join(args.filter)
    pattern_filter = re.compile(filters)

    # files to process
    to_process = get_files_from_paths(args.input_paths, recurse=args.recurse, pattern_filter=pattern_filter)

    # exit if no files were specified
    if not to_process:
        logger.warning(f'No log files specified!')
        sys.exit(1)

    # get output file path
    if args.output_file != '-':
        output_file_path = Path(args.output_file)

        # if the output file is a directory, add /output.json to the path
        if os.path.isdir(output_file_path):
            current_date = datetime.datetime.now().strftime('%Y-%m-%d.%H-%M-%S')
            output_file_path = Path(os.path.join(output_file_path, f'output-{current_date}.json'))

        # if output directory does not exist, create it
        out_dir = output_file_path.parent.absolute()
        if not os.path.isdir(out_dir):
            logger.debug(f'Creating output directory \'{out_dir}\'')

            try:
                os.makedirs(out_dir, exist_ok=True)
            except:
                logger.exception(f'Unable to create the output directory \'{out_dir}\'!')
                sys.exit(1)

        if os.path.exists(output_file_path) and not args.force:
            logger.error(f'Output file \'{output_file_path}\' already exists!')
            sys.exit(1)

    result = {}

    if args.fast:
        result = parse_files_regex(to_process, mfip=args.mfip, lfip=args.lfip, eps=args.eps, count_bytes=args.bytes, exclude_header_sizes=args.exclude_header_sizes)
    else:
        result = parse_files_pandas(to_process, mfip=args.mfip, lfip=args.lfip, eps=args.eps, count_bytes=args.bytes, exclude_header_sizes=args.exclude_header_sizes)

    if args.output_file == '-':
        print(json.dumps(result, indent=4))
    else:
        with open(output_file_path, 'w') as output:
            output.write(json.dumps(result, indent=4))

if __name__ == '__main__':
    run()
