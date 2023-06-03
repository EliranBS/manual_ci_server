FROM python:3.10-alpine
WORKDIR /ci
RUN apk add docker && apk add docker-compose && apk add git 
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN mkdir /test
COPY app.py .
COPY /home/ubuntu/.ssh/id_rsa.pub .

ENTRYPOINT ["python3", "app.py"]
