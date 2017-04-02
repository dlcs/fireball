#!/bin/bash

service nginx restart

cd /opt/fireball && uwsgi --ini /opt/fireball/fireball.ini

