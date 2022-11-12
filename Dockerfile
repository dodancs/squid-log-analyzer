# use Python 3 on alpine
FROM python:3.10-alpine

# set the current working directory to /data
WORKDIR /data

# install requirements
# optimized for speed
RUN apk add --update --no-cache py3-pandas
ENV PYTHONPATH=/usr/lib/python3.10/site-packages

# COPY ./requirements.txt /tmp/requirements.txt
# RUN apk --no-cache --virtual .deps add musl-dev linux-headers g++ && \
#     pip install -r /tmp/requirements.txt && \
#     rm -f /tmp/requirements.txt && \
#     apk del .deps && \
#     apk add --no-cache musl

# copy the script and make it executable
COPY ./analyzer.py /analyzer.py
RUN chmod +x /analyzer.py

# make the /data directory a volume
VOLUME ["/data"]

# set the entrypoint
ENTRYPOINT ["/analyzer.py"]

# show help by default
CMD ["-h"]
