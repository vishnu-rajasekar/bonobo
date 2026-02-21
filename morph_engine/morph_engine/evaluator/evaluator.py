import inspect


class Evaluator:
    def __init__(self, channels):
        self.channels = channels

    def evaluate(self, graph):
        context = {}
        metrics = {}
        signals = {}
        for channel in self.channels:
            signature = inspect.signature(channel.evaluate)
            if "context" in signature.parameters:
                out = channel.evaluate(graph, context=context)
            else:
                out = channel.evaluate(graph)
            context[channel.name] = out
            metrics.update(out.get("metrics", {}))
            signals.update(out.get("signals", {}))

        overall_valid = all(result.get("valid", True) for result in context.values())
        return {
            "valid": overall_valid,
            "channels": context,
            "metrics": metrics,
            "signals": signals,
        }
