import json

class Command:
    def __init__(self, name, args={}):
        self.name = name
        self.args = args

    def to_json(self):
        return json.dumps(self.__dict__)