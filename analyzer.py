#! /usr/bin/env python3

import logging
import argparse
import os
import sys
import re
from pathlib import Path
import datetime
import json


# global variables
logger = None


def prepare_filters(filters = []):
    """Prepare regex pattern by combining all filters in an or statement.

    Args:
        filters (list, optional): List of regex filters. Defaults to [].

    Returns:
        re.Pattern: Compiled regex pattern.
    """
    if not filters:
        return re.compile('.*')

    try:
        # if a signle filter is supplied, return it
        if len(filters) == 1:
            return re.compile(filters[0])

        # join multiple filters with an or statement like so: (filter1)|(filter2)
        return re.compile('(' + ')|('.join(filters) + ')')
    except Exception as ex:
        logger.error(f'Filter pattern is invalid!')
        logger.error(f'RegEx: {ex}')
        sys.exit(1)


def get_files_from_paths(paths, recurse = False, pattern_filter = re.compile('.*')):
    """Get a list of files to process form a list of paths.

    Args:
        paths (list): List of paths.
        recurse (bool, optional): Whether to look for files in subdirectories or not. Defaults to False.
        pattern_filter (re.Pattern, optional): RegEx pattern to filter discovered file paths. Defaults to re.compile('.*').

    Returns:
        list: A list of file paths to process.
    """

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

            # check if the file has already been added
            if absolute_path in to_process:
                continue

            # check if the file can be opened
            try:
                with open(absolute_path, 'r') as f:
                    f.close()
            except:
                logger.debug(f'Unable to read file \'{absolute_path}\'!')
                continue

            # add file
            logger.debug(f'Adding file \'{p}\'.')
            to_process.append(absolute_path)
            continue

        # if path is a directory, search through it
        if os.path.isdir(p):

            # go through paths in directory
            for pp in os.listdir(p):
                subpath = os.path.join(p, pp)

                # process files
                if os.path.isfile(subpath):
                    if subpath in paths:
                        continue

                    paths.append(subpath)
                    continue

                # process directories
                if os.path.isdir(subpath):

                    # skip directory if recursion not allowed
                    if not recurse:
                        logger.debug(f'Skipping subdirectory \'{subpath}\'.')
                        continue

                    # check if the directory has already been added
                    if subpath in paths:
                        continue

                    # also process files in subdirectory recursively
                    paths.append(subpath)
                    continue

                # if path does not exist, show error
                logger.debug(f'Unable to access path \'{subpath}\'!')

        # if path does not exist, show error
        logger.debug(f'Unable to access path \'{p}\'!')

    return to_process


def prepare_output_file(file_path, force):
    """Prepare the output file

    Args:
        file_path (str): Original file path specified by the user. Can be a directory or a file.
        force (bool): Whether to force overwrite the destination file.

    Returns:
        pathlib.Path: Path to the output file or None if the file exists and forceful override was not enabled.
    """

    if file_path == '-':
        return None

    output_file_path = Path(file_path)

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

    if os.path.exists(output_file_path) and not force:
        logger.error(f'Output file \'{output_file_path}\' already exists!')
        sys.exit(1)

    return output_file_path


def init_argparser():
    """Initialize the ArgumentParser library to accept commandline options.

    Returns:
        argparse.ArgumentParser: Initialized ArgumentParser object.
    """

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
    """Initialize the logger.

    Args:
        level (logging._Level): Logging level (info, debug, ...).
    """

    global logger

    logger = logging.getLogger()
    logger.setLevel(level)
    logger_handler = logging.StreamHandler(sys.stdout)
    logger_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(logger_handler)


def parse_files_pandas(to_process, mfip = False, lfip = False, eps = False, count_bytes = False, exclude_header_sizes = False):
    """Parse and analyze files with pandas.

    Args:
        to_process (list): List of file paths to analyze.
        mfip (bool, optional): Analyze the most frequent IP addresses. Defaults to False.
        lfip (bool, optional): Analyze the least frequent IP addresses. Defaults to False.
        eps (bool, optional): Analyze the number of events and number of events per second. Defaults to False.
        count_bytes (bool, optional): Count the total number of bytes transmitted. Defaults to False.
        exclude_header_sizes (bool, optional): Whether to exclude HTTP header sizes. Defaults to False.

    Returns:
        dict: Dictionary containing the analysis results.
    """

    import pandas

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


def parse_files_regex(to_process, mfip = False, lfip = False, eps = False, count_bytes = False, exclude_header_sizes = False):
    """Parse and analyze files with regex

    Args:
        to_process (list): List of file paths to analyze.
        mfip (bool, optional): Analyze the most frequent IP addresses. Defaults to False.
        lfip (bool, optional): Analyze the least frequent IP addresses. Defaults to False.
        eps (bool, optional): Analyze the number of events and number of events per second. Defaults to False.
        count_bytes (bool, optional): Count the total number of bytes transmitted. Defaults to False.
        exclude_header_sizes (bool, optional): Whether to exclude HTTP header sizes. Defaults to False.

    Returns:
        dict: Dictionary containing the analysis results.
    """

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
    """Main function for setting up the tool and running the analysis.
    """

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

    # prepare pattern filter
    pattern_filter = prepare_filters(args.filter)

    # files to process
    to_process = get_files_from_paths(args.input_paths, recurse=args.recurse, pattern_filter=pattern_filter)

    # exit if no files were specified
    if not to_process:
        logger.warning(f'No log files specified!')
        sys.exit(1)

    # get output file path
    output_file_path = prepare_output_file(args.output_file, args.force)

    # use regex parser if --fast option is set
    file_parser = parse_files_pandas
    if args.fast:
        file_parser = parse_files_regex

    result = file_parser(to_process, mfip=args.mfip, lfip=args.lfip, eps=args.eps, count_bytes=args.bytes, exclude_header_sizes=args.exclude_header_sizes)

    # print to stdout if '-' was supplied as output file path
    if not output_file_path:
        print(json.dumps(result, indent=4), flush=True)
        sys.exit(0)

    # write results to the output file
    try:
        with open(output_file_path, 'w') as output:
            output.write(json.dumps(result, indent=4))
    except:
        logger.debug(f'Unable to write output file \'{output_file_path}\'!')
        sys.exit(1)

if __name__ == '__main__':
    run()
