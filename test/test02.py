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
    path_get='/kv/get'

    def setUp(self):
        with open('../conf/settings.conf') as f:
            d = json.load(f)
            self.url = 'http://'+d['primary']+':'+d['port']

    def testone(self):
        payload = {'key': 'sha cha&+="*#@$++---====+++', 'value' :'he he'} # test space
        r = requests.post(self.url+self.path_insert, data=payload)
        print(r.text)
        payload = {'key': '韩国人越南人', 'value' :'和谐'} # test Chinese
        r = requests.post(self.url+self.path_insert, data=payload)
        print(r.text)

    def getter(self):
        payload = {'key': 'sha cha&+="*#@$++---====+++'}
        r = requests.get(self.url+self.path_get, params=payload)
        print(r.url)
        print(r.text)
        


if __name__ == '__main__':
    unittest.main()

