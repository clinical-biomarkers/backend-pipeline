FROM python:3.10.4

WORKDIR /app

ENV FLASK_APP=bmkb

ENV FLASK_ENV=production


WORKDIR /app

COPY ./requirements.txt .

RUN pip3 install -r requirements.txt

COPY ./dist/bmkb-1.0-py3-none-any.whl .

RUN pip3 install bmkb-1.0-py3-none-any.whl

RUN mkdir -p /data/shared/biomarkerdb

RUN mkdir -p /usr/local/var/bmkb-instance

COPY ./instance/config.py /usr/local/var/bmkb-instance/config.py

COPY . .

ENTRYPOINT FLASK_APP=bmkb gunicorn -b :80 'bmkb:create_app()'



