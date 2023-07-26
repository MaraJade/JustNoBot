# -----
# Tests
# -----

FROM python:3 AS tester

RUN mkdir /app/

COPY dbmigration.py /app
COPY dumpfile.sql /app
COPY justnobot.py /app
COPY requirements.txt /app
COPY config.py /app
COPY tests/test_database.py /app


RUN apt update && apt upgrade -y
RUN apt install python3-dev libpq-dev -y

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

WORKDIR /app

CMD ["python3", "test_database.py"]

# ----------
# Production
# ----------

FROM python:3 AS builder

COPY --from=tester /app /app

WORKDIR /app

RUN apt update && apt upgrade -y
RUN apt install python3-dev libpq-dev -y

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

CMD ["python3", "justnobot.py"]
