class Channel:
    name = ""

    def evaluate(self, graph):
        """
        Returns:
        {
            "valid": bool,
            "metrics": dict,
            "signals": dict
        }
        """
        raise NotImplementedError
