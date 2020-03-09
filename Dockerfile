FROM python:3.7-slim

LABEL Name=exact_time
EXPOSE 5000

WORKDIR /app

COPY exact_time /app/exact_time
COPY config.py /app

RUN pip install -r exact_time/deploy/requirements.txt

ENV QUART_CONFIG config.py

ENTRYPOINT ["hypercorn", "--bind", "0.0.0.0:5000", "exact_time/service:app"]
