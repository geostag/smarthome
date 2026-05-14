FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY sensors/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY sensors/bin /app/bin
COPY sensors/sensors-entrypoint.sh /usr/local/bin/sensors-entrypoint.sh

RUN chmod +x /usr/local/bin/sensors-entrypoint.sh

CMD ["sensors-entrypoint.sh"]
