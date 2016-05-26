import html
import http.client
import io
import mimetypes
import os
import posixpath
import select
import shutil
import socket # For gethostbyaddr()
import socketserver
import sys
import time
import urllib.parse
import copy
import argparse
import re
import signal
import json
import xmlrpc.client

import requests

import garage

from http import HTTPStatus

from http.server import BaseHTTPRequestHandler

class PrimaryHTTPRequestHandler(BaseHTTPRequestHandler):

    """Simple HTTP request handler with GET and HEAD commands.

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
        if self.path == '/backup/copy': # this should be deleted
            tries = 20
            while tries:
                time.sleep(0.01)
                tries=tries-1
                backup_rpc = self.connect_backup()
                if backup_rpc:
                    backup_rpc.set_main_mem(garage.main_mem)
                    backup_rpc.set_time_stamp(garage.time_stamp[0])

        if self.path == '/kvman/shutdown':
            os.remove('conf/primary.pid')
            os.kill(os.getpid(),signal.SIGINT)
        if self.path == '/kvman/countkey':
            return self.str2file('{"result": "'+str(garage.countkey())+'"}')
        if self.path == '/kvman/dump':
            return self.dict2file(garage.dump())
        if self.path == '/kvman/gooddump':
            return self.str2file('{"main_mem": '+json.dumps(garage.main_mem)+', "time_stamp": "'+str(garage.time_stamp[0])+'"}')
        if self.path == '/':
            return self.str2file('<h1>Test</h1>')
        pattern = re.compile('/kv/get\?key=(?P<the_key>.+)')
        m = pattern.match(self.path)
        if m:
            the_key = m.group('the_key')
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
        #print(the_key,the_value)
        if self.path == '/kv/insert':
            if the_key and the_value:
                myold_t = garage.time_stamp[0]
                ret = garage.insert(the_key,the_value)
                if ret:
                    proxy = self.connect_backup()
                    if proxy: # the following time_diff claues may be useless, but is correct. if time complexity is bad, remove them
                        time_diff = myold_t - proxy.get_time_stamp()
                        if time_diff > 0:
                            proxy.set_main_mem(garage.main_mem)
                            proxy.set_time_stamp(garage.time_stamp[0])
                        else:
                            proxy.insert(the_key,the_value)
                            if time_diff < 0:
                                garage.main_mem = proxy.dump()
                                garage.time_stamp[0] = proxy.get_time_stamp()
                            else:
                                proxy.set_time_stamp(garage.time_stamp[0])
                return self.str2file('{"success":"'+str(ret).lower()+'"}')
        elif self.path == '/kv/delete':
            if the_key:
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

    def guess_type(self, path):
        """Guess the type of a file.

        Argument is a PATH (a filename).

        Return value is a string of the form type/subtype,
        usable for a MIME Content-type header.

        The default implementation looks the file's extension
        up in the table self.extensions_map, using application/octet-stream
        as a default; however it would be permissible (if
        slow) to look inside the data to make a better guess.

        """

        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']

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

    if not mimetypes.inited:
        mimetypes.init() # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream', # Default
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
        })
