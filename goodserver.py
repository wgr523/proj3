import io
import os
import shutil
import socket # For gethostbyaddr()
import sys
import time
import re
import signal
import json
import xmlrpc.client
from urllib.parse import unquote_plus
import requests

from http import HTTPStatus

from http.server import BaseHTTPRequestHandler

import garage

class PrimaryHTTPRequestHandler(BaseHTTPRequestHandler):

    """HTTP request handler with GET and HEAD and POST commands.

    This serves files from the current directory and any of its
    subdirectories.  The MIME type for files is determined by
    calling the .guess_type() method.

    The GET and HEAD requests are identical except that the HEAD
    request omits the actual contents of the file.

    """

    server_version = "GeruiHTTP/0.0.3"

    backup_address = None # string
    backup_port = None # string
    
    def do_GET(self):
        """Serve a GET request."""
        f = self.simple_get()
        try:
            self.copyfile(f, self.wfile)
        finally:
            f.close()

    def do_HEAD(self):
        """Serve a HEAD request."""
        f = self.send_head()
        if f:
            f.close()

    def do_POST(self):
        f = self.simple_post()
        try:
            self.copyfile(f, self.wfile)
        finally:
            f.close()

    def connect_backup(self):
        if not self.backup_address or not self.backup_port:
            f = open('conf/settings.conf')
            d = json.load(f)
            self.backup_address = d['backup']
            self.backup_port = d['port']
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.1)
            s.connect((self.backup_address, int(self.backup_port)))
            s.close()
        except:
            return None
        url = 'http://'+self.backup_address+':'+self.backup_port
        proxy = xmlrpc.client.ServerProxy(url)
        return proxy

    def simple_get(self):
        if self.path == '/back':
            backup_rpc = self.connect_backup()
            if backup_rpc:
                return self.str2file('Backup online')
            else:
                return self.str2file('Backup offline')

        if self.path == '/kvman/shutdown':
            try:
                f = open('conf/primary.pid')
                pid = int(f.readline())
                f.close()
                os.remove('conf/primary.pid')
                os.kill(pid,signal.SIGKILL)
            except:
                try:
                    os.kill(os.getpid(),signal.SIGKILL)
                except:
                    pass
            exit(0)

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

    def simple_post(self):
        length = self.headers.get('content-length')
        try:
            nbytes = int(length)
        except (TypeError, ValueError):
            nbytes = 0
        if nbytes >0:
            data = self.rfile.read(nbytes) # data is bytes not string
        else:
            return None
        the_key=None
        the_value=None
        inputs = data.decode(sys.getfilesystemencoding()).split('&')
        for tmpstr in inputs:
            tmpinput = tmpstr.split('=')
            if tmpinput[0]=='key':
                the_key=tmpinput[1]
            elif tmpinput[0]=='value':
                the_value=tmpinput[1]
        #print(str(data))
        #print('the key and value are',the_key,the_value)
        if self.path == '/kv/insert':
            if the_key and the_value:
                the_key = unquote_plus(the_key)
                the_value = unquote_plus(the_value)
                myold_t = garage.get_time_stamp()
                ret = garage.insert(the_key,the_value)
                mynew_t = time.time()
                garage.set_time_stamp(mynew_t)
                if ret:
                    proxy = self.connect_backup()
                    if proxy: # below I consider what if RPC backup is wrong (not necessarily shutdown) (exception happens)
                        yourold_t = None
                        try:
                            yourold_t = proxy.get_time_stamp() # what if exception happens here? yourold_t will be None
                            time_diff = myold_t - yourold_t #proxy.get_time_stamp()
                            if time_diff == 0:
                                proxy.insert(the_key,the_value)
                                proxy.set_time_stamp(mynew_t)
                            elif time_diff > 0:
                                proxy.set_main_mem(garage.dump()) # what if exception happens here? it's ok because I am newer
                                proxy.set_time_stamp(garage.get_time_stamp()) # ditto
                            else:
                                proxy.insert(the_key,the_value)# what if exception happens here? ok because below we (p and b) both delete (and set back time)
                                proxy.set_time_stamp(mynew_t)
                                garage.set_main_mem(proxy.dump())
                                garage.set_time_stamp(mynew_t)

                            '''what if proxy insert false? don't care, because next action will handle
                            what if exception happens here? note that this WILL update proxy's time stamp
                            if ptime == btime (time_diff==0): ok because below we (p and b) both delete (and set back time)
                            if ptime < btime (time_diff<0): could this happen??? yes, under partition... see below
                            '''
                        except:
                            garage.delete(the_key)
                            garage.set_time_stamp(myold_t)
                            try:
                                proxy.delete(the_key) # what if exception happens here? don't delete, ok. delete but don't set time, bug happens!!!!! See CAP theorem
                                proxy.set_time_stamp(yourold_t)
                            except:
                                pass
                            return self.str2file('{"success":"false", "info":"Backup connection error."}')
                return self.str2file('{"success":"'+str(ret).lower()+'"}')
        elif self.path == '/kv/delete':
            if the_key:
                the_key = unquote_plus(the_key)
                old_t = garage.time_stamp[0]
                ret = garage.delete(the_key)
                proxy = self.connect_backup()
                if proxy:
                    if proxy.get_time_stamp() < old_t:
                        proxy.set_main_mem(garage.main_mem)
                    else:
                        proxy.delete(the_key)
                    proxy.set_time_stamp(garage.time_stamp[0])
                return self.str2file('{"success":"'+str(ret[0]).lower()+'","value":"'+ret[1]+'"}')
        elif self.path == '/kv/update':
            if the_key and the_value:
                the_key = unquote_plus(the_key)
                the_value= unquote_plus(the_value)
                old_t = garage.time_stamp[0]
                ret = garage.update(the_key,the_value)
                proxy = self.connect_backup()
                if proxy:
                    if proxy.get_time_stamp() < old_t:
                        proxy.set_main_mem(garage.main_mem)
                    else:
                        proxy.update(the_key,the_value)
                    proxy.set_time_stamp(garage.time_stamp[0])
                return self.str2file('{"success":"'+str(ret).lower()+'"}')
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

