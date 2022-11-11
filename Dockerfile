# use Python 3 on alpine
FROM python:3.10-alpine

# set the current working directory to /data
WORKDIR /data

# copy the script and make it executable
COPY ./analyzer.py /analyzer.py
RUN chmod +x /analyzer.py

# make the /data directory a volume
VOLUME ["/data"]

# set the entrypoint
ENTRYPOINT ["/analyzer.py"]

# show help by default
CMD ["-h"]
