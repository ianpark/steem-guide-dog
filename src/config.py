import json

class Config(dict):
    data = {}
    def __init__(self, path):
        with open(path) as data_file:    
            self.data = json.load(data_file)

    def get(self, key):
        return self.data.get(key, '')