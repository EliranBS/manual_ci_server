FROM python:3.10-alpine
WORKDIR /monitoring
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY monitoring.py .

ENTRYPOINT ["python3", "monitoring.py"]
