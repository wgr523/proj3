import requests, json
import unittest
import os
from time import sleep
import subprocess
from subprocess import Popen
from threading import Thread
import threading
def parse_output(r,k):
    if not r or not r.text:
        return None
    #print(r.text)
    output = json.loads(r.text)
    if k in output:
        return output[k]
    else:
        return None

class TestStringMethods:
    url = ''
    path_insert='/kv/insert'
    path_update='/kv/update'
    path_delete='/kv/delete'
    path_get='/kv/get?key='
    insertlatency = []
    getlatency = []
    totinsert = [0]
    sucinsert = [0]
    def assertEqual(self, a1, a2):
        if a1 != a2:
           ifsucceed[0] = 0; 
           return 0
        else:
           return 1

    def __init__(self):
        with open('conf/settings.conf') as f:
            d = json.load(f)
            self.url = 'http://'+d['primary']+':'+d['port']

    def do_insert(self,payload):    
        r = requests.post(self.url+self.path_insert, data=payload)
        self.insertlatency.append(r.elapsed)
        equalresult = self.assertEqual(parse_output(r,'success'),'true')
        self.totinsert[0] = self.totinsert[0]+1
        self.sucinsert[0] = self.sucinsert[0]+equalresult
        #print('Insert success')

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
        self.getlatency.append(r.elapsed)
        self.assertEqual(parse_output(r,'success'),'true')
        return 'This is output of do_get:  ' + parse_output(r,'value')

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
    
    def do_dump(self):
        r = requests.get(self.url+'/kvman/dump') #problematic
        return r

    # This is xpd1's part

    def fork_insert(self,id):
        self.do_insert({'key': 'HandsomeXuwei'+str(id), 'value': str(id*10)})
    def fork_insertFail(self,id):
        self.od_insert({'key': 'HandsomeXuwei'+str(id), 'value': str(id*10)})
    def fork_get(self,id):
        #print(self.do_get('HandsomeXuwei'+str(id)))
        self.do_get('HandsomeXuwei'+str(id))
    def fork_update(self,id,value):
        self.do_update({'key': 'HandsomeXuwei'+str(id), 'value': str(value)})
    def testTeacher1(self):
        '''
        os.chdir('..');
        proc = Popen('python primary_server.py', shell=True,
             stdin=None, stdout=None, stderr=None, close_fds=True)
        proc = Popen('python backup_server.py', shell=True,
             stdin=None, stdout=None, stderr=None, close_fds=True)
        '''

        global ifsucceed
        ifsucceed = [1]
        medemede = 100

        #pP = Popen(['python', 'primary_server.py'], cwd='..', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) # something long running
        #pB = Popen(['python', 'backup_server.py'], cwd='..', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) # something long running
        os.system('bin/start_server -p')
        os.system('bin/start_server -b')

        sleep(1)
        
        threadid = [0]
        for i in range(1,medemede+1):
            threadid.append(Thread(self.fork_insert(i)))
            threadid[i].start()

        for i in range(1,medemede+1):
            threadid[i].join()

        
        #r = requests.get(self.url+'/kvman/countkey')
        #self.assertEqual(parse_output(r,'result'),str(1))
        #print('countkey OK ' + str(medemede))

        for i in range(1,medemede+1):
            threadid[i] = Thread(self.fork_get(i))
            threadid[i].start()
        for i in range(1,medemede+1):
            threadid[i].join()

        sleep(1)
        #pP.terminate()
        #pB.terminate()
        os.system('bin/stop_server -p')
        os.system('bin/stop_server -b')

        
        if ifsucceed[0] == 1:
           print('Result: success')
        else:
           print('Result: fail')
        
        print('Insertion: '+str(self.sucinsert[0]) + '/' +str(self.totinsert[0]) )
        self.insertlatency.sort()
        self.getlatency.sort()
        print('Percentile latency: ' 
            + str(self.insertlatency[round(len(self.insertlatency)*0.8)]) + '/' + str(self.insertlatency[round(len(self.insertlatency)*0.8)]) + ', '
            + str(self.insertlatency[round(len(self.insertlatency)*0.5)]) + '/' + str(self.insertlatency[round(len(self.insertlatency)*0.5)]) + ', '
            + str(self.insertlatency[round(len(self.insertlatency)*0.3)]) + '/' + str(self.insertlatency[round(len(self.insertlatency)*0.3)]) + ', '
            + str(self.insertlatency[round(len(self.insertlatency)*0.1)]) + '/' + str(self.insertlatency[round(len(self.insertlatency)*0.1)]) + ', '
            )
        pass

newTest = TestStringMethods()
newTest.testTeacher1()

