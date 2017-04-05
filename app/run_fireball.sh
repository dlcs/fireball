#!/bin/bash

service nginx restart

touch /log/fireball.log

mkdir -p /scratch/fireball

cd /opt/fireball && uwsgi --ini /opt/fireball/fireball.ini &

tail -f /log/fireball.log
