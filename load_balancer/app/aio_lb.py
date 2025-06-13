import asyncio, os, logging
from aiohttp import web, ClientSession, ClientTimeout

logging.basicConfig(level=logging.INFO)

HOST = os.getenv("HOST", "localhost")
PORTS_ENV = os.getenv("PORTS", "5001-5005")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 5))
PROBE_TIMEOUT   = float(os.getenv("PROBE_TIMEOUT", 0.5))

PORT_QUEUE: asyncio.Queue[int] = asyncio.Queue()
OFFLINE: set[int] = set()

def _expand(port_str: str) -> list[int]:
    """Преобразует `5001-5005,5010` → [5001,5002,5003,5004,5005,5010]"""
    res = []
    for part in port_str.split(","):
        if "-" in part:
            a, b = map(int, part.split("-"))
            res.extend(range(a, b + 1))
        else:
            res.append(int(part))
    return res

for p in _expand(PORTS_ENV):
    PORT_QUEUE.put_nowait(p)

async def health_monitor():
    """Периодически проверяет OFFLINE-порты и реанимирует живые."""
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
                            await PORT_QUEUE.put(port)
                            logging.info("Port %s is back online", port)
                except Exception:
                    pass



async def index(request: web.Request):
    """Выбирает живой порт и делает 302 Redirect."""
    max_attempts = PORT_QUEUE.qsize() + len(OFFLINE)
    attempt = 0
    while attempt < max_attempts:
        port = await PORT_QUEUE.get()
        attempt += 1

        if port in OFFLINE:

            continue


        timeout = ClientTimeout(total=PROBE_TIMEOUT)
        async with ClientSession(timeout=timeout) as session:
            try:
                url = f"http://{HOST}:{port}/health"
                async with session.get(url) as r:
                    if r.status == 204:

                        await PORT_QUEUE.put(port)

                        raise web.HTTPFound(f"http://{HOST}:{port}/")
            except Exception:
                OFFLINE.add(port)
                logging.warning("Port %s marked OFFLINE", port)

    raise web.HTTPServiceUnavailable(text="No back-end servers available")

async def port_update(request: web.Request):
    """Получает ping от backend'а после обработки запроса."""
    port = int(request.match_info["port"])
    if port in OFFLINE:
        OFFLINE.remove(port)
    if port not in PORT_QUEUE._queue:
        await PORT_QUEUE.put(port)
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
