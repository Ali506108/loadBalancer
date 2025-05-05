FROM python:3.12-alpine

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir flask

EXPOSE 8001

CMD ["flask", "run", "--host=0.0.0.0", "--port=8001"]
