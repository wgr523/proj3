import json
import os
from xmlrpc.server import SimpleXMLRPCServer
import garage
def test():
    return True
def run(address ='127.0.0.2', portnumber = 8001):
    server_class=SimpleXMLRPCServer
    server_address = (address,portnumber)
    server = server_class(server_address)
    server.register_function(garage.insert,"insert")
    server.register_function(garage.update,"update")
    server.register_function(garage.delete,"delete")
    server.register_function(garage.get,"get")
    server.register_function(garage.countkey,"countkey")
    server.register_function(garage.dump,"dump")
    server.register_function(test,"test")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
def start_p():
    with open('conf/settings.conf') as f:
        d = json.load(f)
        run(d['backup'],int(d['port']))
with open('conf/backup.pid','w') as fout:
    fout.write(str(os.getpid()))
start_p()
