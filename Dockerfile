FROM python:3.6

COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt \
    && groupadd -r admin && useradd -r -g admin admin

EXPOSE 8000

USER admin

ENV ENV_TYPE=PRODUCTION

ENTRYPOINT [ "python", "run.py"]
