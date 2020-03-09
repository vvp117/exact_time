FROM python:3.7-slim

LABEL Name=exact_time
EXPOSE 5000

WORKDIR /app

COPY exact_time /app/exact_time
COPY config.py /app

RUN pip install -r /app/exact_time/deploy/requirements.txt

ENV QUART_APP /app/exact_time/service:app
ENV QUART_CONFIG /app/config.py

ENTRYPOINT ["quart", "run", "-h", "0.0.0.0", "-p", "5000"]
