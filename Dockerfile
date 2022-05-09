# Section 1- Base Image
FROM python:3.10.4-slim


# Section 2- Python Interpreter Flags

ENV PYTHONDONTWRITEBYTECODE=1\
    PYTHONUNBUFFERED=1\
    POETRY_VERSION=1.1.13

WORKDIR /app

RUN pip install "poetry==$POETRY_VERSION"
RUN apt-get update && apt-get install -y gcc libffi-dev g++ libpq-dev python3-dev

# Project libraries and User Creation

COPY poetry.lock pyproject.toml /app/


RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

COPY ./docker/entrypoint.sh /app/docker/entrypoint.sh

RUN pip3 install --upgrade pip setuptools wheel
RUN pip install psycopg2-binary
RUN python3 -m pip install Pillow

COPY . /app/

RUN chmod +x /app/docker/entrypoint.sh
