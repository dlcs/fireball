#!/bin/bash

service nginx restart

touch /log/fireball.log

cd /opt/fireball && uwsgi --ini /opt/fireball/fireball.ini &

tail -f /log/fireball.log