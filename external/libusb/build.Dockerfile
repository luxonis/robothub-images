FROM ubuntu:22.04

RUN apt-get update -qq \
    && apt-get install -qq -y --no-install-recommends ca-certificates wget bzip2 build-essential \
    && rm -rf /var/lib/apt/lists/*
