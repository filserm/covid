import requests
import json

class Api():
    
    def __init__(self, url):
        self.url = url
    
    def set_session(self):
        self.session = requests.Session()
    
    def parse_response(self):
        self.response = self.session.get(self.url)
        return json.loads(self.response.text, object_hook = lambda dict: DictWithAttributeAccess(dict))
        

class DictWithAttributeAccess(dict):
    def __getattr__(self, key):
        return self[key]
 
    def __setattr__(self, key, value):
        self[key] = value


if __name__ == '__main__':
    url = 'https://api.corona-zahlen.org/germany'
    api_instance = Api(url)
    api_instance.set_session()
    r = api_instance.parse_response()

    print (json.dumps(r, sort_keys=True, indent=4))