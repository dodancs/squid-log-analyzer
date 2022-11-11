# Simple Squid log analyzer

![](https://img.shields.io/github/workflow/status/dodancs/squid-log-analyzer/Build%20Docker%20image?label=Docker%20Image%20Build&style=for-the-badge)

## About this project

This is a simple application allowing any user to analyze the contents of Squid logs and report some statistics in the form of a JSON file.

## Building this project

There are some prerequisites listed below that are needed for the project to run:

- Python 3 <u>(Python 2 is not supported)</u>
- Docker *(optional)*

You can run this command directly from your terminal like so:

```bash
$ git clone https://github.com/dodancs/squid-log-analyzer.git
$ cd squid-log-analyzer
$ python3 squid-log-analyzer.py --help
```

But if you want, you can also build it as a Docker image:

```bash
$ git clone https://github.com/dodancs/squid-log-analyzer.git
$ cd squid-log-analyzer
$ docker build -t squid-log-analyzer .
```

After the Docker image is built, you can run a Docker container like so:

```bash
$ docker run --rm squid-log-analyzer --help
```

If you don't want to build it yourself, you can use an existing Docker image from the Github Package Repository:

```bash
docker run --rm ghcr.io/dodancs/squid-log-analyzer:latest --help
```

## Using this project

You can print the usage documentation anytime by using the `--help` or `-h` argument:

```bash
$ squid-log-analyzer.py --help

usage: squid-log-analyzer.py [-h] [-v] [--filter FILTER] [-r] [-f] [--mfip] [--lfip] [--eps] [--bytes] INPUT [INPUT ...] OUTPUT
```

All of the arguments are described below.

#### Positional arguments:

| Argument    | Description | Example    |
|-------------|-------------|------------|
| `INPUT`<br />`[INPUT ...]` | Paths to files or directories that contain log files. If a directory is specified, all of the files in that directory will be added for analysis.<br />The user may also specify multiple paths for the INPUT, in which case the tool will analyze all of the paths supplied. | `logs.txt` or `logs/` |
| `OUTPUT` | Path to the output file or directory. If a directory is specified, a new file with the current timestamp (`output-YYYY-MM-DD.HH-MM-SS.json`) will be created in that directory. If the path supplied does not exist, all of the parent directories will be created automatically. | `output.json` |

#### Optional arguments:

| Argument    | Description | Example    |
|-------------|-------------|------------|
| `-h`<br />`--help` | Show the usage documentation for the tool and exit. |  |
| `-v`<br />`--verbose` | Show verbose log output. The tool will print a lot of information to help you debug what is happening. |  |
| `--filter FILTER` | [RegEx](https://www.w3schools.com/python/python_regex.asp) filter pattern for file names. **Only files that match a filter will be analyzed.** You can also supply multiple filter patterns to match more files.<br>*Note: Filters work with the absolute file paths.* | `--filter '\.txt$'` `--filter '\.log$'` |
| `-r`<br />`--recurse` | Enable directory recursion. Files in sub-directories will also be included in analysis. | For input of `-r` `./dir`, any files in `./dir/dir2`, `./dir/dir2/dir3` as well as all other will be added. |
| `-f`<br />`--force` | Overwrite the output file if it already exists. **This action is irreversible.** |  |
| `--exclude-header-sizes` | Do not count the bytes sent in the headers section of an HTTP request. Only bytes transfered in the body of the request will be taken into account.<br />**This argument is to be used together with `--bytes`.** |  |

#### Operations:

| Argument    | Description |
|-------------|-------------|
| `--mfip` | Analyze the **most frequent** IP address present in the log files. |
| `--lfip` | Analyze the **least frequent** IP address present in the log files. |
| `--eps` | Count the number of events per second. |
| `--bytes` | Count the total number of bytes exchanged.<br />Can be used together with `--exclude-header-sizes` to only count transmitted bytes in the body of each request. |

## Input log file example

The tool is designed to analyze logs from the Squid HTTP cache and proxy. A log file line usually looks like this:

```log
1157689324.156 1372 10.105.21.199 TCP_MISS/200 399 GET http://www[.]google-analytics[.]com/__utm.gif? badeyek DIRECT/66.102.9.147 image/gif
```

The individual fields are described below:

- **Field 1**: `1157689324.156` [Timestamp in seconds since the epoch]
- **Field 2**: `1372` [Response header size in bytes]
- **Field 3**: `10.105.21.199` [Client IP address]
- **Field 4**: `TCP_MISS/200` [HTTP response code]
- **Field 5**: `399` [Response size in bytes]
- **Field 6**: `GET` [HTTP request method]
- **Field 7**: `http://www.google-analytics.com/__utm.gif?` [URL]
- **Field 8**: `badeyek` [Username]
- **Field 9**: `DIRECT/66.102.9.147` [Type of access/destination IP address] Field 10: image/gif [Response type]


## Understanding the report output

The tool generates output in plaintext JSON format which can be easily used by any other tools or read directly by humans without further processing.

\# TODO: Show JSON output and explain

## Example usage

Here are a few examples of the tool in action, so you can quickly learn how to use its features.

#### File input and output

The tool requires at least one `INPUT` path and one `OUTPUT` path. Both of these paths can be either a file or a directory. Here are a few examples:

```bash
$ squid-log-analyzer.py ./logs ./report.json
# Files from ./logs/ will be processed, and the output will be written to ./report.json
$ squid-log-analyzer.py /var/log/squid/* ./
# Files from /var/log/squid/ will be processed, the output will be written to ./output-YYYY-MM-DD.HH-MM-SS.json
$ squid-log-analyzer.py -r logs1 /tmp/squid/output.json
# Files from logs1 and its subdirectories will be processed, and the output will be written to /tmp/squid/output.json
```

If the output file does not exist, it will be created, as well as all of its parent directories.

#### Filtering files based on RegEx patterns

You can supply a [regular expression pattern](https://www.w3schools.com/python/python_regex.asp) to the tool to filter which files are allowed to be analyzed:

```bash
$ squid-log-analyzer.py --filter '\.txt$' ./logs ./report.json
# Only files from ./logs/ that end with the '.txt' text will be processed.
$ squid-log-analyzer.py --filter '\.txt$' --filter '\.log$' ./logs ./report.json
# Only files from ./logs/ that end with the '.txt' or '.log' text will be processed.
$ squid-log-analyzer.py -r --filter '(squid|apache)' /var/log ./report.json
# Files from /var/log and all subdirectories that contain 'squid' or 'apache' text in their paths will be processed.
```

####  Analyze the logs

To actually do anything useful, you need to specify at least one of the allowed operations - `--mfip`, `--lfip`, `--eps`, `--bytes`. Multiple operations can be run at the same time and their results will be included in the report output.

```bash
$ squid-log-analyzer.py --mfip --eps --bytes ./logs.txt ./report.json
# File logs.txt will be analyzed and the most frequent IP address, the number of events per second and total bytes exchanged will be included in the report.json file.
```
