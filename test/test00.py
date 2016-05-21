import requests, json
import unittest
import os
from time import sleep

def parse_output(r,k):
    if not r or not r.text:
        return None
    #print(r.text)
    output = json.loads(r.text)
    if k in output:
        return output[k]
    else:
        return None

class TestMethods(unittest.TestCase):
    url = ''
    path_insert='/kv/insert'
    path_update='/kv/update'
    path_delete='/kv/delete'
    path_get='/kv/get?key='

    def setUp(self):
        with open('../conf/settings.conf') as f:
            d = json.load(f)
            self.url = 'http://'+d['primary']+':'+d['port']

    def testone(self):
        payload = {'key': 'rinima', 'value' :'2222'}
        r = requests.post(self.url+self.path_insert, data=payload)
        print(r.text)
        payload = {'key': 'dalailama', 'value' :'23333'}
        r = requests.post(self.url+self.path_insert, data=payload)
        print(r.text)


if __name__ == '__main__':
    unittest.main()

