FROM selenium/node-base:3.14.0-helium
MAINTAINER drunkar <drunkars.p@gmail.com>


##############################################################################
# node chrome
##############################################################################
USER root
#============================================
# Google Chrome
#============================================
# can specify versions by CHROME_VERSION;
#  e.g. google-chrome-stable=53.0.2785.101-1
#       google-chrome-beta=53.0.2785.92-1
#       google-chrome-unstable=54.0.2840.14-1
#       latest (equivalent to google-chrome-stable)
#       google-chrome-beta  (pull latest beta)
#============================================
# at first install chrome to install dependencies which are also required for chromium
ENV CHROME_VERSION="google-chrome-stable"
RUN cat /etc/os-release
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
  && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
  && apt-get update -qqy \
  && apt-get -qqy install \
    ${CHROME_VERSION:-google-chrome-stable} \
  && rm /etc/apt/sources.list.d/google-chrome.list \
  && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

# wget --no-verbose http://ftp.ubuntu.com/ubuntu/ubuntu/pool/universe/c/chromium-browser/chromium-browser_61.0.3163.100-0ubuntu1.1378_amd64.deb
COPY chromium-codecs-ffmpeg_61.0.3163.100-0ubuntu1.1378_amd64.deb ./
COPY chromium-codecs-ffmpeg-extra_61.0.3163.100-0ubuntu1.1378_amd64.deb ./
COPY chromium-browser_61.0.3163.100-0ubuntu1.1378_amd64.deb ./
RUN apt update \
  && apt remove -y google-chrome-stable \
  && sudo dpkg -i chromium-codecs-ffmpeg_61.0.3163.100-0ubuntu1.1378_amd64.deb \
  && sudo dpkg -i chromium-codecs-ffmpeg-extra_61.0.3163.100-0ubuntu1.1378_amd64.deb \
  && sudo dpkg -i chromium-browser_61.0.3163.100-0ubuntu1.1378_amd64.deb \
  && sudo apt-mark hold chromium-browser

RUN chromium-browser --version

#=================================
# Chrome Launch Script Wrapper
#=================================
COPY wrap_chrome_binary /opt/bin/wrap_chrome_binary
RUN /opt/bin/wrap_chrome_binary


#============================================
# Chrome webdriver
#============================================
# can specify versions by CHROME_DRIVER_VERSION
# Latest released version will be used by default
#============================================
COPY chromium-chromedriver_61.0.3163.100-0ubuntu1.1378_amd64.deb ./
RUN apt update \
  && rm -rf /opt/selenium/chromedriver \
  && sudo dpkg -i chromium-chromedriver_61.0.3163.100-0ubuntu1.1378_amd64.deb \
  && sudo apt-mark hold chromium-chromedriver

RUN cat /usr/lib/chromium-browser/chromedriver | sed -e 's/cdc_asdjflasutopfhvcZLmcfl_/xxx_asdjflasutopfhvcZLmcfl_/g' > /opt/selenium/chromedriver-mod \
  && mv /usr/lib/chromium-browser/chromedriver /usr/lib/chromium-browser/chromedriver_org \
  && mv /opt/selenium/chromedriver-mod /opt/selenium/chromedriver \
  && chmod 755 /opt/selenium/chromedriver \
  && ln -fs /opt/selenium/chromedriver /usr/bin/chromedriver

USER seluser
COPY generate_config /opt/bin/generate_config

# Generating a default config during build time
RUN /opt/bin/generate_config > /opt/selenium/config.json


##############################################################################
# node chrome debug
##############################################################################
USER root

#=====
# VNC
#=====
RUN apt-get update -qqy \
  && apt-get -qqy install \
  x11vnc \
  && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

#=========
# fluxbox
# A fast, lightweight and responsive window manager
#=========
RUN apt-get update -qqy \
  && apt-get -qqy install \
    fluxbox \
  && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

USER seluser

#==============================
# Generating the VNC password as seluser
# So the service can be started with seluser
#==============================

RUN mkdir -p ${HOME}/.vnc \
  && x11vnc -storepasswd secret ${HOME}/.vnc/passwd

#==========
# Relaxing permissions for OpenShift and other non-sudo environments
#==========
RUN sudo chmod -R 777 ${HOME} \
  && sudo chgrp -R 0 ${HOME} \
  && sudo chmod -R g=u ${HOME}

#==============================
# Scripts to run fluxbox and x11vnc
#==============================
COPY start-fluxbox.sh \
      start-vnc.sh \
      /opt/bin/

#==============================
# Supervisor configuration file
#==============================
COPY selenium-debug.conf /etc/supervisor/conf.d/

EXPOSE 5900



##############################################################################
# standalone chrome debug
##############################################################################
USER seluser

#====================================
# Scripts to run Selenium Standalone
#====================================
COPY start-selenium-standalone.sh /opt/bin/start-selenium-standalone.sh

#==============================
# Supervisor configuration file
#==============================
COPY selenium.conf /etc/supervisor/conf.d/


EXPOSE 4444
EXPOSE 5900



##############################################################################
# settings
##############################################################################

# Install wget and build-essential
USER root
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
