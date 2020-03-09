FROM python:3.7-slim

LABEL Name=exact-time
EXPOSE 5000

WORKDIR /app

# add and install requirements
COPY ./deploy/requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

# add app
COPY . .

ENTRYPOINT ["hypercorn", "--bind", "0.0.0.0:5000", "service:app"]
