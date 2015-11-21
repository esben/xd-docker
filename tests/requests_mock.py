import json


class Response(object):
    def __init__(self, text, status_code):
        self.text = text
        self.status_code = status_code

    def iter_lines(self):
        return [line.encode('utf-8') for line in self.text.split('\n')]

    def json(self):
        return json.loads(self.text)
