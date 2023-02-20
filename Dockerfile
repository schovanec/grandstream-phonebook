FROM python:3

RUN pip install vobject vdirsyncer cron-converter

WORKDIR /scripts

COPY src/ ./

ENV PATH /scripts:$PATH
ENV PYTHONUNBUFFERED true

ENTRYPOINT ["./run.sh"]
