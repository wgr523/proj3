import sys
import json
import os
from http.server import HTTPServer
from goodserver import PrimaryHTTPRequestHandler
import xmlrpc.client
import garage

def connect_backup():
    f = open('conf/settings.conf')
    d = json.load(f)
    backup_url='http://'+d['backup']+':'+d['port']
    try:
        proxy = xmlrpc.client.ServerProxy(backup_url)
        proxy.test()
        return proxy
    except:
        return None

def run(handler_class, address ='127.0.0.1', portnumber = 8001):
    server_class=HTTPServer
    server_address = (address,portnumber)
    httpd = server_class(server_address,handler_class)
    proxy = connect_backup()
    if proxy:
        print('backup connected, copying')
        garage.main_mem = proxy.dump()
        print('copied')
    else:
        print('backup offline')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
def start_p():
    with open('conf/settings.conf') as f:
        d = json.load(f)
        run(PrimaryHTTPRequestHandler,d['primary'],int(d['port']))
with open('conf/primary.pid','w') as fout:
    fout.write(str(os.getpid()))
start_p()
