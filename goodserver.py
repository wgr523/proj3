import io
import os
import shutil
import socket # For gethostbyaddr()
import sys
import time
import re
import signal
import threading
import json
import xmlrpc.client
from urllib.parse import unquote_plus
import requests
import collections

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
#self.server
    server_version = "GeruiHTTP/0.0.3"
    backup_address = None
    backup_port = None
    proxy = None

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
            self.backup_address = self.server.backup_address
            self.backup_port = self.server.backup_port
        if self.proxy:
            return self.proxy
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.1)
            s.connect((self.backup_address, int(self.backup_port)))
            s.close()
        except:
            return None
        url = 'http://'+self.backup_address+':'+self.backup_port
        self.proxy = xmlrpc.client.ServerProxy(url)
        return self.proxy

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

        if self.path == '/kvman/countkey':
            with garage.mutex:
                f = self.str2file('{"result": "'+str(garage.countkey())+'"}')
            return f
        if self.path == '/kvman/dump':
            with garage.mutex:
                f = self.dict2file(garage.dump())
            return f
        if self.path == '/kvman/gooddump':
            with garage.mutex:
                f = self.str2file('{"main_mem": '+json.dumps(garage.main_mem)+', "time_stamp": "'+str(garage.get_time_stamp())+'"}')
                garage.clear_fail_backup()
            return f
        if self.path == '/':
            return self.str2file('Test<br>This is primary<br>Client address: '+str(self.client_address)+'<br>Thread: '+threading.currentThread().getName())
        pattern = re.compile('/kv/get\?key=(?P<the_key>.+)')
        m = pattern.match(self.path)
        if m:
            the_key = m.group('the_key')
            the_key = unquote_plus(the_key)
            rw_lock = garage.get_rw_create(the_key)
            rw_lock.before_read()
            ret = garage.get(the_key)
            f = self.str2file('{"success":"'+str(ret[0]).lower()+'","value":'+json.dumps(ret[1])+'}')
            rw_lock.after_read()
            return f
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
                rw_lock = garage.get_rw_create(the_key)
                rw_lock.before_write()
                ret = garage.insert(the_key,the_value)
                if ret:
                    proxy = self.connect_backup()
                    if proxy:
                        #self.check_syn(proxy)
                        try:
                            proxy.insert_no_matter_what(the_key,the_value)
                            self.check_syn(proxy)
                        except:
                            garage.delete(the_key)
                            try:
                                proxy.delete(the_key)
                            except:
                                pass
                            rw_lock.after_write()
                            self.check_syn(proxy)
                            return self.str2file('{"success":"false", "info":"Backup connection error."}')
                    else:
                        garage.fail_backup(the_key)
                rw_lock.after_write()
                return self.str2file('{"success":"'+str(ret).lower()+'"}')
        elif self.path == '/kv/delete':
            if the_key:
                the_key = unquote_plus(the_key)
                rw_lock = garage.get_rw_create(the_key)
                rw_lock.before_write()
                ret = garage.delete(the_key)
                if ret[0]:
                    proxy = self.connect_backup()
                    if proxy:
                        #self.check_syn(proxy)
                        try:
                            proxy.delete(the_key)
                            self.check_syn(proxy)
                        except:
                            garage.insert(the_key,ret[1])
                            try:
                                proxy.insert_no_matter_what(the_key,ret[1])
                            except:
                                pass
                            rw_lock.after_write()
                            self.check_syn(proxy)
                            return self.str2file('{"success":"false", "info":"Backup connection error."}')
                    else:
                        garage.fail_backup(the_key)
                rw_lock.after_write()
                return self.str2file('{"success":"'+str(ret[0]).lower()+'","value":"'+ret[1]+'"}')
        elif self.path == '/kv/update':
            if the_key and the_value:
                the_key = unquote_plus(the_key)
                the_value= unquote_plus(the_value)
                rw_lock = garage.get_rw_create(the_key)
                rw_lock.before_write()
                myold_v = garage.get(the_key)
                ret = garage.update(the_key,the_value)
                if ret:
                    proxy = self.connect_backup()
                    if proxy:
                        #self.check_syn(proxy)
                        try:
                            proxy.insert_no_matter_what(the_key,the_value)
                            self.check_syn(proxy)
                        except:
                            garage.update(the_key,myold_v)
                            try:
                                proxy.insert_no_matter_what(the_key,myold_v)
                            except:
                                pass
                            rw_lock.after_write()
                            self.check_syn(proxy)
                            return self.str2file('{"success":"false", "info":"Backup connection error."}')
                    else:
                        garage.fail_backup(the_key)
                rw_lock.after_write()
                return self.str2file('{"success":"'+str(ret).lower()+'"}')
        return self.str2file('{"success":"false"}')

    def check_syn(self,proxy):
        with garage.mutex:
            l = garage.list_fail_backup()
            mem = garage.dump()
            for key in l:
                if key in mem:
                    v=mem[key]
                    try:
                        proxy.insert_no_matter_what(key,v)
                        garage.delete_fail_backup(key)
                    except Exception as err:
                        print(err)
                        pass
                else:
                    try:
                        proxy.delete(key)
                        garage.delete_fail_backup(key)
                    except Exception as err:
                        print(err)
                        pass


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
        od = collections.OrderedDict(sorted(d.items()))
        for key,value in od.items():
            r.append('['+json.dumps(key)+','+json.dumps(value)+']')
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

