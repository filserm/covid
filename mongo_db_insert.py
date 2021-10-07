import json, os
from pymongo import MongoClient

class Mongo():

    def __init__(self, cluster, database, collection):
        self.username = os.getenv('MONGO_USER')
        self.password = os.getenv('MONGO_PW')
        self.cluster = cluster
        self.database = database
        self.collection = collection
    
    def connect(self):
        self.conn_str = f'mongodb+srv://{self.username}:{self.password}@{self.cluster}/{self.database}?retryWrites=true&w=majority'
        self.client = MongoClient(self.conn_str, serverSelectionTimeoutMS=5000)
        print (self.client.server_info()['version'])
        self.db = self.client[self.database]
        self.collection = self.db[self.collection]
    
    def insert_json(self, datafile):
        with open(datafile) as f:
            file_data = json.load(f)
            self.collection.insert_one(file_data)
    
    def insert(self, data):
        try:
            self.collection.insert_one(data)
            return True
        except Exception as e:
            print("An exception occurred ::", e)
            return False

if __name__ == "__main__":
    testdb = Mongo(
        cluster = 'cluster0.tr5bj.mongodb.net'
        , database = 'rain'
        , collection = 'weatherdata'
    )
    testdb.connect()
    testdb.insert(datafile='data.json')



