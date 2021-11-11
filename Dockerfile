FROM python:3

RUN pip install vobject vdirsyncer

WORKDIR /scripts

COPY src/ ./

ENV VDIRSYNCER_CONFIG=/data/config
ENV PATH /scripts:$PATH

ENTRYPOINT ["./run.sh"]
