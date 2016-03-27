FROM docker:1.10

RUN apk add --update \
    python3 python3-dev build-base \
 && rm -rf /var/cache/apk/*
RUN wget "https://bootstrap.pypa.io/get-pip.py" -O /dev/stdout | python3 \
 && pip install --upgrade pip

COPY requirements.txt /
COPY tests/requirements.txt /test-requirements.txt
RUN pip install -r requirements.txt -r test-requirements.txt
