FROM amazonlinux:latest

LABEL maintainer="keith@keithrozario.com"

RUN yum install libtool perl-core zlib-devel -y && \
    yum install wget bzip gzip tar -y && \
    yum group install "Development Tools" "Development Libraries" -y && \
    yum group install "AWS Tools" -y && \
    yum install python3.x86_64 python3-pip python3-devel.x86_64 -y && \
    yum install jq nano -y

RUN pip3 install --upgrade pip
