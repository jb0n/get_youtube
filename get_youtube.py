#!/usr/bin/env python

'''
Script to download youtube videos and organize them (if possible).
'''

import cherrypy

#from pyechonest import song, artist

from youtubedl_wrapper import YoutubeDlWrapper

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
            ret = fix_text(ydw.download())
            if ret['err']:
                args['text'] += ret['text']
                return PAGE % args

        return PAGE % args
    index.exposed = True

if __name__ == '__main__':
    cherrypy.server.socket_host = ADDR
    cherrypy.quickstart(GetYoutube())

