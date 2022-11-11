# use Python 3 on alpine
FROM python:3.10-alpine

# set the current working directory to /data
WORKDIR /data

# copy the script and make it executable
COPY ./main.py /main.py
RUN chmod +x /main.py

# make the /data directory a volume
VOLUME ["/data"]

# set the entrypoint
ENTRYPOINT ["/main.py"]

# show help by default
CMD ["-h"]
