import sys
import json
import os
from http.server import HTTPServer
from goodserver import PrimaryHTTPRequestHandler
import xmlrpc.client
import socket 
import garage

def connect_backup():
    f = open('conf/settings.conf')
    d = json.load(f)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.1)
        s.connect((d['backup'], int(d['port'])))
        s.close()
    except:
        return None
    backup_url='http://'+d['backup']+':'+d['port']
    proxy = xmlrpc.client.ServerProxy(backup_url)
    return proxy

def run(handler_class, address , portnumber ):
    server_class=HTTPServer
    server_address = (address,portnumber)
    httpd = server_class(server_address,handler_class)
    proxy = connect_backup()
    if proxy:
        print('backup connected')
        t = proxy.get_time_stamp()
        if t:
            print('copying')
            garage.main_mem = proxy.dump()
            garage.time_stamp[0] = t
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
