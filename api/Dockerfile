FROM python:3.7-alpine
WORKDIR /usr/source/app
ENV FLASK_APP=main.py
ENV FLASK_RUN_HOST=0.0.0.0
COPY requirements.txt requirements.txt
RUN apk update && apk add build-base && \
 apk add python3-dev && \
 apk add --no-cache postgresql-libs bash && \
 apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
 python3 -m pip install -r requirements.txt --no-cache-dir && \
 apk --purge del .build-deps
EXPOSE 5000
COPY . .
RUN chmod +x wait-for-it.sh
CMD ["./wait-for-it.sh" , "rabbitmq:15672" , "--timeout=35" , "--" , "flask", "run"]