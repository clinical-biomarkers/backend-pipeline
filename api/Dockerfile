FROM python:3.10.4

WORKDIR /app

ENV FLASK_APP=bmkb
ENV FLASK_ENV=production

COPY ./requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY ./dist/bmkb-1.0-py3-none-any.whl .
RUN pip3 install --no-cache-dir bmkb-1.0-py3-none-any.whl

RUN groupadd --system appuser \
 && useradd --system --gid appuser --home-dir /app --no-create-home \
      --shell /usr/sbin/nologin appuser \
 && mkdir -p /data/shared/biomarkerdb /usr/local/var/bmkb-instance

COPY --chown=appuser:appuser ./instance/config.py /usr/local/var/bmkb-instance/config.py
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8888

ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:8888", "bmkb:create_app()"]


