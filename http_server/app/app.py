from flask import Flask
from math import factorial
from random import randint
import requests
import os

app = Flask(__name__)


def update_status(my_port):
    lb_ip_addr = os.environ.get("LB_IP_ADDR", "localhost")
    lb_port = os.environ.get("LB_PORT", "8001")

    try:
        return requests.get(f"http://{lb_ip_addr}:{lb_port}/port_update/{my_port}")
    except Exception as e:
        return str(e)


@app.route("/")
@app.route("/<int:my_port>")
def factapp(my_port=None):
    random_value = randint(100, 1000)

    print("random_value", random_value)

    res = str(factorial(random_value))

    return_string = f"Factorial of {random_value} = {res}"

    if my_port is not None:
        update_res = str(update_status(my_port))
        if "200" not in update_res:
            return f'Failed to update port status: {update_res}'

    return return_string


@app.route("/health", methods=["GET"])
def healthcheck():
    """Лёгкий ping-эндпойнт для балансировщика."""
    return "", 204

if __name__ == "__main__":
    app.run()
