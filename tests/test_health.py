import json
from urllib.request import urlopen

from schedule_bot.health import start_health_server


def test_health_endpoint() -> None:
    server = start_health_server(0)
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/healthz", timeout=2) as response:
            assert response.status == 200
            assert json.load(response) == {"status": "ok"}
    finally:
        server.shutdown()
        server.server_close()

