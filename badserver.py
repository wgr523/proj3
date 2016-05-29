import io
import os
import shutil
import signal
import sys
import json

from http import HTTPStatus

from xmlrpc.server import SimpleXMLRPCRequestHandler

import garage

class HTTPAndRPCRequestHandler(SimpleXMLRPCRequestHandler):
    ''' extends RPC Handler
    added HTTP GET feature
    '''

    rpc_paths = ('/RPC2',)

    def do_GET(self):
        """Serve a GET request."""
        f = self.simple_get()
        try:
            self.copyfile(f, self.wfile)
        finally:
            f.close()

    def simple_get(self):
        if self.path == '/kvman/shutdown':
            try:
                f = open('conf/backup.pid')
                pid = int(f.readline())
                f.close()
                os.remove('conf/backup.pid')
                os.kill(pid,signal.SIGKILL)
            except:
                try:
                    os.kill(os.getpid(),signal.SIGKILL)
                except:
                    pass

        if self.path == '/kvman/countkey':
            return self.str2file('{"result": "'+str(garage.countkey())+'"}')
        if self.path == '/kvman/dump':
            return self.dict2file(garage.dump())
        if self.path == '/kvman/gooddump':
            return self.str2file('{"main_mem": '+json.dumps(garage.main_mem)+', "time_stamp": "'+str(garage.time_stamp[0])+'"}')
        if self.path == '/':
            return self.str2file('<h1>Test</h1><br>Client address: '+str(self.client_address))
        pattern = re.compile('/kv/get\?key=(?P<the_key>.+)')
        m = pattern.match(self.path)
        if m:
            the_key = m.group('the_key')
            the_key = unquote_plus(the_key)
            ret = garage.get(the_key)
            return self.str2file('{"success":"'+str(ret[0]).lower()+'","value":"'+ret[1]+'"}')
        return self.str2file('{"success":"false"}')
    
    def copyfile(self, source, outputfile):
        """Copy all data between two file objects.

        The SOURCE argument is a file object open for reading
        (or anything with a read() method) and the DESTINATION
        argument is a file object open for writing (or
        anything with a write() method).

        The only reason for overriding this would be to change
        the block size or perhaps to replace newlines by CRLF
        -- note however that this the default server uses this
        to copy binary data as well.

        """
        shutil.copyfileobj(source, outputfile)    

    def dict2file(self,d):
        ''' d is dictionary, similar to str2file(). by wgr'''
        r = []
        enc = sys.getfilesystemencoding()
        for key in d:
            r.append('["'+key+'","'+d[key]+'"]')
        the_string = '['+', '.join(r)+']'
        encoded = the_string.encode(enc, 'surrogateescape')
        f = io.BytesIO()
        f.write(encoded)
        f.seek(0)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-type", "text/html; charset=%s" % enc)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        return f

    def str2file(self,word):
        ''' print string to a file by wgr'''
        enc = sys.getfilesystemencoding()        
        encoded = word.encode(enc, 'surrogateescape')
        f = io.BytesIO()
        f.write(encoded)
        f.seek(0)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-type", "text/html; charset=%s" % enc)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        return f


