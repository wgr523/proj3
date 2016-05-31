import requests, json
import unittest
import os
from time import sleep
import threading
from threading import Thread


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
    lock = threading.RLock()
    abn=0
    def setUp(self):
        with open('../conf/settings.conf') as f:
            d = json.load(f)
            self.url = 'http://'+d['primary']+':'+d['port']

    def getter(self):
        payload = {'key': 'sha cha&+="*#@$++---====+++'}
        r = requests.get(self.url+self.path_get, params=payload)
        print(r.url)
        print(r.text)
    def func(self):
        tmp = threading.currentThread().getName()
        payload = {'key': tmp, 'value' :'1'}
        try:
            r = requests.post(self.url+self.path_insert, data=payload)
           # if parse_output(r.text,'success') == 'false':
           #     with self.lock:
           #         self.abn=self.abn+1
        except:
            #with self.lock:
                #self.abn=self.abn+1
            print('wrong')
    def testmanymany(self):
        #payload = {'key': 'BB', 'value' :'-1'}
        #r = requests.post(self.url+self.path_insert, data=payload)
        lu = 50
        tt=[]
        for i in range(lu):
            t = Thread(target = self.func)
            tt.append(t)
            t.start()
        for t in tt:
            t.join()
        print(self.abn)
        

        


if __name__ == '__main__':
    unittest.main()

