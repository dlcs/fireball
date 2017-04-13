#!/bin/bash

service nginx restart

touch $FIREBALL_LOGFILE

cd /opt/fireball && uwsgi --ini /opt/fireball/fireball.ini &

tail -f $FIREBALL_LOGFILE
