FROM ubuntu:22.04

ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update
RUN apt-get install -y ffmpeg libsm6 libxext6 libgl1 libglib2.0-0

RUN apt update
RUN apt install -y python3.10
RUN apt install -y python3-pip
RUN apt install -y ghostscript python3-tk