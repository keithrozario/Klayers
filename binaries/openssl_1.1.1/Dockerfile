FROM lambci/lambda-base:build

LABEL maintainer="keith@keithrozario.com"

RUN yum install libtool perl-core zlib-devel -y && \
    yum install wget -y

WORKDIR /tmp/build

RUN wget https://www.openssl.org/source/openssl-1.1.1c.tar.gz && \
    tar -zxvf openssl-1.1.1c.tar.gz && \
    cd openssl-1.1.1c && \
    ./config --prefix=/opt --openssldir=/opt shared zlib && \
    make && make test && make install

RUN mkdir /tmp/layer && \
    cp -R /opt/bin/ /tmp/layer && \
    cp -R /opt/lib/ /tmp/layer
