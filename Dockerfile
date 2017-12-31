FROM selenium/standalone-chrome-debug
MAINTAINER drunkar <drunkars.p@gmail.com>

USER root

# Install wget and build-essential
RUN apt-get update && apt-get install -y \
  build-essential \
  wget

##############################################################################
# anaconda python
##############################################################################
# Install Anaconda
RUN apt-get update && \
    apt-get install -y wget bzip2 ca-certificates

RUN wget --quiet https://repo.continuum.io/archive/Anaconda3-4.4.0-Linux-x86_64.sh && \
    /bin/bash Anaconda3-4.4.0-Linux-x86_64.sh -b -p /opt/conda && \
    rm Anaconda3-4.4.0-Linux-x86_64.sh

ENV PATH /opt/conda/bin:$PATH
RUN pip install --upgrade pip


ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

WORKDIR /usr/src/app
VOLUME ["/usr/src/app"]

USER seluser
