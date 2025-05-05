FROM python:3.12-alpine

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir flask requests

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
