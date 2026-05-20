import json

class mDb:
    def __init__(self,path,**kwargs):
        self.path = path
        self.autoflush = kwargs.get("autoflush",True)
        self.DB = {}
        try:
            self.read()
        except:
            print(f"WARNING: could not read database from '{self.path}', starting with defaults")

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.write()

    def write(self):
        with open(self.path,'w', encoding='utf-8') as f:
            json.dump(self.DB, f, ensure_ascii=False, indent=2)

    def read(self):
        with open(self.path, 'r') as f:
            self.DB = json.load(f)

    @property
    def hash(self):
        return self.DB

    @hash.setter
    def hash(self,h):
        self.DB = h
        if self.autoflush:
            self.write()

    def set(self,key,value):
        self.DB[key] = value
        if self.autoflush:
            self.write()

    def get(self,key,default=None):
        return self.DB.get(key,default)

