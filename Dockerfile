# -----
# Tests
# -----

FROM python:3 AS tester

RUN mkdir /app/

ADD justnobot.py /app
ADD requirements.txt /app
ADD config.py /app
ADD tests/test_database.py /app


RUN apt update && apt upgrade -y
RUN apt install sqlite3 -y

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

WORKDIR /app

CMD ["python3", "test_database.py"]

# ----------
# Production
# ----------

FROM python:3 AS builder

COPY --from=tester /app /app
#ADD justnobot.py /
#ADD config.py /
#ADD requirements.txt /
ADD justno.db /app

WORKDIR /app

#RUN apt update && apt upgrade -y
#RUN apt install sqlite3 -y

#RUN pip install --no-cache-dir --upgrade pip && \
#    pip install --no-cache-dir -r requirements.txt

CMD ["python3", "justnobot.py"]


