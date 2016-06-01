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
        tmp = 'd'+threading.currentThread().getName()[7:]
        payload = {'key': tmp, 'value' :tmp+'哈'}
        try:
            r = requests.post(self.url+self.path_insert, data=payload)
            if parse_output(r,'success') == 'false':
                with self.lock:
                    self.abn=self.abn+1
            for i in range(10):
                payload = {'key': tmp}
                r = requests.get(self.url+self.path_get, params=payload)
                if parse_output(r,'success') == 'false':
                    with self.lock:
                        self.abn=self.abn+1
            for i in range(0):
                payload = {'key': tmp, 'value' :str(i+10)}
                r = requests.post(self.url+self.path_update, data=payload)
                if parse_output(r,'success') == 'false':
                    with self.lock:
                        self.abn=self.abn+1
#            payload = {'key': tmp}
#            r = requests.post(self.url+self.path_delete, data=payload)
#            if parse_output(r,'success') == 'false':
#                with self.lock:
#                    self.abn=self.abn+1
#            payload = {'key': tmp, 'value' : '-1'}
#            r = requests.post(self.url+self.path_insert, data=payload)
        except Exception as err:
            print(err)
            with self.lock:
                self.abn=self.abn+1
    def testmanymany(self):
        #payload = {'key': 'BB', 'value' :'-1'}
        #r = requests.post(self.url+self.path_insert, data=payload)
        lu = 1000
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

