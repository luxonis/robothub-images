import json
from json import *
from datetime import datetime


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.astimezone().isoformat()
        else:
            return str(obj)


def dumps(*args, **kwargs):
    return json.dumps(*args, **kwargs, cls=JSONEncoder)


def dump(*args, **kwargs):
    return json.dump(*args, **kwargs, cls=JSONEncoder)
