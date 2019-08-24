FROM amazonlinux:latest

LABEL maintainer="keith@keithrozario.com"

RUN yum install libtool perl-core zlib-devel -y && \
    yum install wget bzip gzip tar -y && \
    yum group install "Development Tools" "Development Libraries" -y && \
    yum group install "AWS Tools" -y