FROM python:3.10.5

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN python -m nltk.downloader punkt

COPY . .

CMD ["python", "./main.py"]