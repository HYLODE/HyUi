# pull official base image
FROM python:3.9-slim-buster

# set working directory
WORKDIR /usr/src

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update \
  && apt-get -y install netcat gcc postgresql \
  && apt-get clean

# install python dependencies
RUN pip install --upgrade pip
COPY ./app/requirements.txt .
RUN pip install -r requirements.txt

# loading environment variables into docker image
# is managed at the docker-compose level 

# add app from local dash directory to WORKDIR (above)
# COPYING means directories are created at build time
# UNCOMMENT if you want a standalone dockerfile
# COPY dash dash

# BUT the PREFERRED default is to add as mount volumes via docker-compose
# AND THEN run using docker-compose
# docker-compose up --build dash