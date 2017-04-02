FROM ubuntu

RUN apt-get update -y && apt-get install -y python-pip python-dev build-essential nginx uwsgi
COPY app /opt/fireball
COPY etc/fireball.nginx.conf /etc/nginx/sites-available/fireball
RUN ln -s /etc/nginx/sites-available/fireball /etc/nginx/sites-enabled/fireball && rm -f /etc/nginx/sites-enabled/default
RUN pip install -r /opt/fireball/requirements.txt
WORKDIR /opt/fireball
CMD /opt/fireball/run_fireball.sh
EXPOSE 80
