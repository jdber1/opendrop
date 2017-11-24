from abc import ABCMeta


def controlled_by(presenter_class):
    def decorator(controllable):
        return controllable

    return decorator

def handler(event_name):
    def decorator(method):
        setattr(method, '_presenter_handler_tag', event_name)

        return method

    return decorator