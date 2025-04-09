"""Mock contextvars module for compatibility with earlier versions of Python."""


def copy_context():
    return Context()


class Context:
    def run(self, callthing, *args, **kwargs):
        return callthing(*args, **kwargs)
