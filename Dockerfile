FROM python:3.10-alpine

RUN apk add --update --no-cache --virtual=run-deps \
  jpeg-dev \
  zlib-dev \
  build-base \
  gcc \
  linux-headers \
  ca-certificates

WORKDIR /opt/fireball

CMD [ "uwsgi", "--plugins", "http,python3", "--http", "0.0.0.0:80", "--module", "wsgi" ]

EXPOSE 80
COPY requirements.txt /opt/fireball/requirements.txt
RUN pip3 install --no-cache-dir -r /opt/fireball/requirements.txt
COPY app /opt/fireball
