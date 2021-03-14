from files import exist, isdir, readJson, writeJson

class Config:
    def __init__(self, path, data={}):
        self.path = path
        if not exist(self.path):
            writeJson(self.path, data)
            self.data = data
        elif isdir(self.path):
            raise IsADirectoryError(f"'{self.path}' is a directory")
        else:
            self.data = readJson(self.path)
    def update(self):
        self.data = readJson(self.path)
    def save(self):
        writeJson(self.path, self.data)
    def clear(self):
        self.data = {}
        self.save()
    def get(self, key):
        self.update()
        return self.data[key]
    __getitem__ = get
    def set(self, key, value):
        if key not in self.data or value != self.get(key):
            self.data[key] = value
            self.save()
    __setitem__ = set