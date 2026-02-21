import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from registry import TOOLS   # import registry, not tools

PORT = 8765



def register_tool(name):
    def decorator(func):
        TOOLS[name] = func
        return func
    return decorator


class MCPHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8")
        request = json.loads(raw)

        try:
            result = self.dispatch(request)
            self.respond(200, {"ok": True, "result": result})
        except Exception as e:
            self.respond(500, {"ok": False, "error": str(e)})

    def dispatch(self, request):
        tool = request.get("tool")
        args = request.get("args", {})

        if tool not in TOOLS:
            raise ValueError(f"Unknown tool: {tool}")

        return TOOLS[tool](**args)


    def respond(self, status, payload):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))


def start_server():
    server = HTTPServer(("localhost", PORT), MCPHandler)
    print(f"MCP server running at http://localhost:{PORT}")
    server.serve_forever()


thread = threading.Thread(target=start_server, daemon=True)
thread.start()

# IMPORTANT: import tools AFTER server is defined
import tools.draw
