FROM python:3.10-alpine

WORKDIR /tmp

COPY ./squid-log-analyzer.py /squid-log-analyzer.py
RUN chmod +x /squid-log-analyzer.py

ENTRYPOINT ["/squid-log-analyzer.py"]
CMD ["-h"]
