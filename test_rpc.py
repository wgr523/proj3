import json
import os
import xmlrpc.client
def outt():
    print('haha')
def test():
    with open('conf/settings.conf') as f:
        d = json.load(f)
        url='http://'+d['backup']+':'+d['port']
        with xmlrpc.client.ServerProxy(url) as proxy:
            print(proxy.outt())
test()
