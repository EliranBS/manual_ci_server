FROM python:3.10-alpine
WORKDIR /monitoring/mailing
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY mailing.py .
ENTRYPOINT ["python3", "mailing.py"]
