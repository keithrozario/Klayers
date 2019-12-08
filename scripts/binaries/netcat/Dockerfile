FROM layerbuilder:latest

LABEL maintainer="keith@keithrozario.com"

WORKDIR /tmp

RUN wget http://sourceforge.net/projects/netcat/files/netcat/0.7.1/netcat-0.7.1.tar.gz && \
    tar -xzvf netcat-0.7.1.tar.gz && \
    cd netcat-0.7.1 && \
    ./configure && \
    make && make install && \
    mkdir /tmp/layer && mkdir /tmp/layer/bin && mkdir /tmp/layer/lib && \
    cp /usr/local/bin/netcat /tmp/layer/bin/ && \
    cp /lib64/libc.so.6 /tmp/layer/lib/ && \
    cp /lib64/ld-linux-x86-64.so.2 /tmp/layer/lib && \
    cd /tmp/layer && \
    zip netcat.zip . -r