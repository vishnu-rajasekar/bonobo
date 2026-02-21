import json
import urllib.request
import pytest
import socket
from urllib.error import URLError
from http.client import RemoteDisconnected


def test_draw_network():
    payload = {
        "tool": "draw_network",
        "args": {
            "nodes": {
                "0": {"xyz": [0, 0, 0]},
                "1": {"xyz": [5, 0, 0]}
            },
            "edges": [["0", "1"]]
        }
    }

    req = urllib.request.Request(
        "http://localhost:8765",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=1) as res:
            data = json.loads(res.read().decode())
            assert data.get("ok") is True

    except (URLError, RemoteDisconnected, socket.error):
        pytest.skip("MCP server not running")
