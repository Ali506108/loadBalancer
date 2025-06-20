import asyncio
import os
import logging
from aiohttp import web, ClientSession, ClientTimeout

logging.basicConfig(level=logging.INFO)

HOST = os.getenv("HOST", "3.83.117.56")
PORTS_ENV = os.getenv("PORTS", "5001,5002,5003")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 5))
PROBE_TIMEOUT = float(os.getenv("PROBE_TIMEOUT", 0.5))

AVAILABLE_PORTS = []
OFFLINE = set()

def _expand(port_str: str) -> list[int]:
    res = []
    for part in port_str.split(","):
        res.append(int(part))
    return res

AVAILABLE_PORTS = _expand(PORTS_ENV)

async def health_monitor():
    timeout = ClientTimeout(total=PROBE_TIMEOUT)
    async with ClientSession(timeout=timeout) as session:
        while True:
            await asyncio.sleep(CHECK_INTERVAL)
            for port in list(OFFLINE):
                url = f"http://{HOST}:{port}/health"
                try:
                    async with session.get(url) as r:
                        if r.status == 204:
                            OFFLINE.remove(port)
                            AVAILABLE_PORTS.append(port)
                            logging.info("Port %s is back online", port)
                except Exception:
                    pass

async def get_next_port():
    while not AVAILABLE_PORTS:
        await asyncio.sleep(0.1)
    port = AVAILABLE_PORTS.pop(0)
    if port not in OFFLINE:
        AVAILABLE_PORTS.append(port)
        return port
    else:
        return await get_next_port()

async def index(request: web.Request):
    port = await get_next_port()
    url = f"http://{HOST}:{port}/"
    logging.info("Redirecting client to: %s", url)
    raise web.HTTPFound(url)

async def port_update(request: web.Request):
    port = int(request.match_info["port"])
    if port in OFFLINE:
        OFFLINE.remove(port)
    if port not in AVAILABLE_PORTS:
        AVAILABLE_PORTS.append(port)
    return web.json_response({"status": "ok"})

app = web.Application()
app.add_routes([
    web.get("/", index),
    web.post("/port_update/{port}", port_update),
    web.get("/port_update/{port}", port_update),
])

app.on_startup.append(lambda app: app.loop.create_task(health_monitor()))

if __name__ == "__main__":
    web.run_app(app, port=8001)