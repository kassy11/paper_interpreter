FROM ubuntu:22.04

COPY . /bot
WORKDIR /bot

RUN apt-get update
RUN apt-get install -y ffmpeg libsm6 libxext6

RUN apt update
RUN apt install -y python3.10
RUN apt install -y python3-pip
RUN apt install -y ghostscript

RUN pip install --upgrade pip
RUN pip install -r requirements.txt