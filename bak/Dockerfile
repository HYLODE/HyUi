# pull official base image
FROM python:3.10-slim

# install system dependencies
RUN apt-get update && apt-get install -y \
    chromium-driver  python3-selenium \
    netcat gcc postgresql \
    python3-psycopg2 libpq-dev \
    && apt-get clean

# set working directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# add and install requirements
COPY ./requirements.txt .
RUN pip install -r requirements.txt
RUN pip install 'dash[testing]'

# add app
COPY . .

# run tests
CMD python -m pytest
