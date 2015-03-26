#!/usr/bin/env python

'''
Script to download youtube videos and organize them (if possible).
'''

import time
import threading

import cherrypy
from cherrypy.process.plugins import Monitor

#from pyechonest import song, artist

from youtubedl_wrapper import YoutubeDlWrapper
from ydl_queue import YdlQueue

DOWNLOAD_DIR = "video/"
ADDR = '0.0.0.0'
PAGE = '''
<HTML>
    <TITLE>Download Youtube Videos</TITLE>
    <BODY>
        <CENTER><H2>Download Youtube Videos</H2></CENTER>
        <FORM name="input" action="" method="post">
            Enter YouTube URL to download: <input type="text" name="url"/>
            <br/>
        </FORM>
        %(text)s
    </BODY>
</HTML>
'''

YDL_QUEUE = YdlQueue()
ERR_QUEUE = YdlQueue()


def download_worker():
    '''
    '''
    ydw = YDL_QUEUE.get()
    if ydw == None:
        return
    ret = fix_text(ydw.download())
    if ret['err']:
        ERR_QUEUE.put(ret['text'])



def fix_text(ret):
    'turn \n into <br/> and make sure one is  on the end'
    ret['text'] = ret['text'].replace('\n', '<br/>')
    if not ret['text'].endswith('<br/>'):
        ret['text'] = ret['text'] + '<br/>'
    return ret


class GetYoutube(object):
    'The webserver class to downlod videos from youtube'
    def index(self, url=None):
        'index/default page'

        args = {'text': ''}

        if url not in (None, ''):
            ydw = YoutubeDlWrapper(url)
            YDL_QUEUE.put(ydw)
            #ret = fix_text(ydw.download())
            #if ret['err']:
            #    args['text'] += ret['text']
            #    return PAGE % args
        entries = YDL_QUEUE.peek_all()
        for entry in entries:
            args['text'] += '%s<br/>' % entry.url

        errors = ERR_QUEUE.peek_all()
        if len(errors):
            args['text'] += '<br/><H2>Errors<a href="clear_errors">(clear)</a></H2>'
            for error in errors:
                args['text'] += '%s<br/>' % error
                
        
        return PAGE % args
    index.exposed = True

    def clear_errors(self):
        '''
        clear error queue
        '''
        ERR_QUEUE.clear()
        raise cherrypy.HTTPRedirect("/")
    clear_errors.exposed = True

def main():
    'do ALL the things'
    cherrypy.server.socket_host = ADDR
    Monitor(cherrypy.engine, download_worker, frequency=1).subscribe()
    cherrypy.quickstart(GetYoutube())


if __name__ == '__main__':
    main()

