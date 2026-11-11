FROM python:3.13-alpine3.24

RUN apk add --update --no-cache --virtual=run-deps \
  jpeg-dev \
  zlib-dev \
  build-base \
  gcc \
  linux-headers \
  ca-certificates

WORKDIR /opt/fireball

CMD [ "uwsgi", "--master", "--http", "0.0.0.0:80", "--http-timeout", "900", "--module", "wsgi", "--processes", "4" ]

EXPOSE 80
COPY requirements.txt /opt/fireball/requirements.txt
RUN pip3 install --no-cache-dir -r /opt/fireball/requirements.txt
COPY app /opt/fireball
