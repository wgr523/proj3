import json
import os
from xmlrpc.server import SimpleXMLRPCServer
import requests
import garage
def run(address , portnumber , primary_address):
    server_class=SimpleXMLRPCServer
    server_address = (address,portnumber)
    server = server_class(server_address, allow_none=True)
    server.register_function(garage.insert,"insert")
    server.register_function(garage.update,"update")
    server.register_function(garage.delete,"delete")
    server.register_function(garage.get,"get")
    server.register_function(garage.countkey,"countkey")
    server.register_function(garage.dump,"dump")
    server.register_function(garage.get_time_stamp,"get_time_stamp")
    server.register_function(garage.set_time_stamp,"set_time_stamp")
    server.register_function(garage.set_main_mem,"set_main_mem")
    try:
        r = requests.get('http://'+primary_address+':'+str(portnumber)+'/kvman/gooddump')
        b = json.loads(r.text)
        garage.main_mem = b['main_mem']
        garage.time_stamp[0]= float(b['time_stamp'])
        print('primary connected, copied')
    except:
        print('primary offline')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
def start_p():
    with open('conf/settings.conf') as f:
        d = json.load(f)
        run(d['backup'],int(d['port']),d['primary'])
with open('conf/backup.pid','w') as fout:
    fout.write(str(os.getpid()))
start_p()
