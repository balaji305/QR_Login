FROM python:3.11

WORKDIR /usr/src/flakApp

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

RUN python -m spacy download en_core_web_sm

EXPOSE 5000

CMD flask run -h 0.0.0.0 -p 5000