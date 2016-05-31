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

class TestStringMethods(unittest.TestCase):
    url = ''
    path_insert='/kv/insert'
    path_update='/kv/update'
    path_delete='/kv/delete'
    path_get='/kv/get?key='

    def setUp(self):
        with open('../conf/settings.conf') as f:
            d = json.load(f)
            self.url = 'http://'+d['primary']+':'+d['port']

    def do_insert(self,payload):
        r = requests.post(self.url+self.path_insert, data=payload)
        self.assertEqual(parse_output(r,'success'),'true')

    def do_update(self,payload):
        r = requests.post(self.url+self.path_update, data=payload)
        self.assertEqual(parse_output(r,'success'),'true')

    def do_delete(self,key):
        payload={'key':key}
        r = requests.post(self.url+self.path_delete, data=payload)
        self.assertEqual(parse_output(r,'success'),'true')
        return parse_output(r,'value')

    def do_get(self, key):
        r = requests.get(self.url+self.path_get+key)
        self.assertEqual(parse_output(r,'success'),'true')
        return parse_output(r,'value')
    
    def od_insert(self,payload):
        r = requests.post(self.url+self.path_insert, data=payload)
        self.assertEqual(parse_output(r,'success'),'false')

    def od_update(self,payload):
        r = requests.post(self.url+self.path_update, data=payload)
        self.assertEqual(parse_output(r,'success'),'false')

    def od_delete(self,key):
        payload={'key':key}
        r = requests.post(self.url+self.path_delete, data=payload)
        self.assertEqual(parse_output(r,'success'),'false')
        return parse_output(r,'value')

    def od_get(self, key):
        r = requests.get(self.url+self.path_get+key)
        self.assertEqual(parse_output(r,'success'),'false')
        return parse_output(r,'value')
    
    def one(self):
        self.do_insert({'key': 'sha', 'value': 'dashabi'})
        self.od_insert({'key': 'sha', 'value': 'bi'})
        self.do_delete('sha')
        self.od_delete('sha')
        self.od_update({'key': 'sha', 'value': '1'})
        self.do_insert({'key': 'sha', 'value': '0'})
        self.od_insert({'key': 'sha', 'value': '00'})
        self.do_update({'key': 'sha', 'value': '1'})
        self.do_update({'key': 'sha', 'value': '2'})
        self.do_update({'key': 'sha', 'value': '3'})
        self.do_update({'key': 'sha', 'value': '4'})


    def testtwo(self):
        pid = os.fork()
        if pid != 0:
            sleep(1)
        self.do_update({'key': 'sha', 'value': str(pid)})
        print (self.do_delete('sha') )
        
    def many(self):
        for i in range(1,90):
            pid = os.fork()
            if pid == 0:
                self.do_insert({'key': str(os.getpid()), 'value': '0'})
                return
            sleep(0.05)
            if pid != 0:
                print (self.do_delete(str(pid)))
            #payload={'key':str(os.getpid())}
            #requests.post(self.url+self.path_delete, data=payload)

    def toomany(self):
        ''' may be too many things will cause bug...'''
        mainpid = os.getpid()
        #self.do_insert({'key': 'oldman', 'value': 'twooo'})
        for i in range(1,6):
            os.fork()
            self.do_insert({'key': str(os.getpid()), 'value': str(os.getpid())})
            sleep(0.001)
            self.do_delete(str(os.getpid()))
        #if mainpid == os.getpid():
            #print(self.do_delete('oldman'))

if __name__ == '__main__':
    unittest.main()

