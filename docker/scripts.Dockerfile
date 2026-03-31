FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY bin /app/bin
COPY schatzkiste /app/schatzkiste
COPY docker/scripts-entrypoint.sh /usr/local/bin/scripts-entrypoint.sh

RUN chmod +x /usr/local/bin/scripts-entrypoint.sh

CMD ["scripts-entrypoint.sh"]
