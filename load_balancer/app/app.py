from flask import Flask, redirect
import json
import time

app = Flask(__name__)

with open('servers.json') as f:
    data = json.load(f)

port_list = data["available_servers"]

def next_available_server():
    global port_list
    while len(port_list) < 1:
        time.sleep(0.01)
    return port_list.pop(0)

@app.route("/port_update/<int:available_port>")
def update_port(available_port):
    global port_list
    print(f"\nAppending new available port: {available_port}", flush=True)
    port_list.append(str(available_port))
    return '200'


@app.route("/health")
def health():
    return '', 204

@app.route("/")
def root():
    return f"I'm backend on port {PORT}"

@app.route("/")
def entrypoint():
    next_port = next_available_server()
    url = f"http://localhost:{next_port}/{next_port}"
    print(f"\nRedirecting client to: {url}", flush=True)
    return redirect(url, code=302)

if __name__ == "__main__":
    app.run()
