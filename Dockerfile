FROM python:3

ADD justnobot.py /
ADD config.py /
ADD requirements.txt ./

#ADD justno.db /

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

CMD ["echo", "'Starting bot'"]
CMD ["python3", "./justnobot.py"]
