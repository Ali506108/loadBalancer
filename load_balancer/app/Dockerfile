FROM python:3.12-alpine

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir aiohttp

EXPOSE 8001

CMD ["python", "load_balancer.py"]
