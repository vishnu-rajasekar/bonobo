# registry.py

TOOLS = {}


def register_tool(name):
    def decorator(func):
        TOOLS[name] = func
        return func
    return decorator
