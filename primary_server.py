import sys
import json
import os
from http.server import HTTPServer
from socketserver import ThreadingMixIn
from goodserver import PrimaryHTTPRequestHandler
import xmlrpc.client
import socket 
import garage

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    pass

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
    server_class = ThreadedHTTPServer
    server_address = (address,portnumber)
    httpd = server_class(server_address,handler_class)
    proxy = connect_backup()
    if not proxy:
        print('backup offline')
    while proxy:
        try:
            t = proxy.get_time_stamp()
            if t:
                print('backup connected, copying')
                garage.set_main_mem(proxy.dump())
                garage.set_time_stamp(t)
                print('copied')
            proxy = None
        except:
            proxy = connect_backup()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
def start_p():
    with open('conf/settings.conf') as f:
        d = json.load(f)
        run(PrimaryHTTPRequestHandler,d['primary'],int(d['port']))
start_p()
