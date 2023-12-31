FROM python:3.8.4-slim-buster

WORKDIR /app

COPY requirements.txt ./
RUN apt update
RUN apt install -y libxml2-dev libxslt-dev python-dev gcc
RUN pip install --no-cache-dir -r requirements.txt

COPY calsync ./calsync

ENTRYPOINT [ "python", "calsync", "-c", "/app/settings/config.ini" ]