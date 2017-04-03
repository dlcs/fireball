#!/bin/bash

service nginx restart

touch /opt/fireball/fireball.log

cd /opt/fireball && uwsgi --ini /opt/fireball/fireball.ini &

tail -f /opt/fireball/fireball.log