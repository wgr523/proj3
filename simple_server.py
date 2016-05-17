import sys
import json
import os
from http.server import HTTPServer
from goodserver import PrimaryHTTPRequestHandler
def run(handler_class, address ='127.0.0.1', portnumber = 8001):
    server_class=HTTPServer
    server_address = (address,portnumber)
    httpd = server_class(server_address,handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
        sys.exit(0)
def start_p():
    with open('conf/settings.conf') as f:
        d = json.load(f)
        run(PrimaryHTTPRequestHandler,d['primary'],int(d['port']))
with open('conf/primary.pid','w') as fout:
    fout.write(str(os.getpid()))
start_p()
