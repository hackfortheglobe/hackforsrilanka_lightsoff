# Section 1- Base Image
FROM python:3.10.4-slim


# Section 2- Python Interpreter Flags
ENV PYTHONDONTWRITEBYTECODE=1\
    PYTHONUNBUFFERED=1\
    POETRY_VERSION=1.1.13

WORKDIR /app

RUN pip install "poetry==$POETRY_VERSION"
RUN apt-get update && apt-get install -y gcc libffi-dev g++ libpq-dev python3-dev ghostscript wget

# install google chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y google-chrome-stable

# install chromedriver
RUN apt-get install -yqq unzip
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

# Project libraries and User Creation
COPY poetry.lock pyproject.toml /app/
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

RUN pip3 install --upgrade pip setuptools wheel
RUN pip install psycopg2-binary
RUN python3 -m pip install Pillow

COPY . /app/

COPY ./docker/entrypoint.sh /app/docker/entrypoint.sh
RUN chmod +x /app/docker/entrypoint.sh
