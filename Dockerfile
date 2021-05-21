FROM python:3

ADD justnobot.py /
ADD config.py /
ADD requirements.txt /
ADD justno.db /home

RUN apt update && apt upgrade -y
RUN apt install sqlite3 -y

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

CMD ["python3", "/justnobot.py"]
