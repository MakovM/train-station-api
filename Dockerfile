FROM python:3.12-alpine3.22
LABEL maintainer="mykola.makovynskyi@gmail.com"

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

