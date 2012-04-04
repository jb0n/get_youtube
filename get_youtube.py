#!/usr/bin/env python

'''
Script so Erin can dl youtube videos into fishsticks Music Video dir.
'''

import os
import shutil
import cherrypy
from subprocess import Popen, PIPE

DOWNLOAD_DIR = "/home/zun/media/music_video/"
ADDR = '0.0.0.0'
PAGE = '''
<HTML>
    <HEAD>Download Youtube Videos</HEAD>
    <TITLE>Download Youtube Videos</TITLE>
    <BODY>
        <FORM name="input" action="" method="post">
            Enter YouTube URL to download: <input type="text" name="url"/>
            <br/>
        </FORM>
        %(text)s
    </BODY>
</HTML>
'''

def get_proc(cmd):
    return Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                 close_fds=True)


class GetYoutube(object):
    def index(self, url=None):
        args = {'text': ''}
        title = '<title>' #youtube title.

        if url not in (None, ''):
            title = None
            cmd = 'youtube-dl --get-title %s' % url
            proc = get_proc(cmd)
            (stdout, stderr) = proc.communicate()
            if proc.returncode == 0:
                stdout = stdout.strip()
                args['text'] = "Downloaded: %s<br/>" % url
                args['text'] += "Name: %s<br/>" % stdout
                title = stdout
            else:
                args['text'] = "ERROR RETURN FROM youtube-dl binary<br/>"

            cmd = 'youtube-dl --get-filename %s' % url
            proc = get_proc(cmd)
            (stdout, stderr) = proc.communicate()
            if proc.returncode != 0:
                args['text'] += "ERROR cmd '%s' failed<br/>" % cmd
            stdout = stdout.strip()
            fname = stdout                
            ext = fname.split('.')[-1]

            dest = os.path.join(DOWNLOAD_DIR, title)
            dest = dest + '.' + ext
            if os.path.exists(dest):
                args['text'] += "ERROR %s already exists<br/>" % dest
                return PAGE % args

            cmd = 'youtube-dl %s' % url
            proc = get_proc(cmd)
            (stdout, stderr) = proc.communicate()
            if proc.returncode != 0:
                args['text'] += "ERROR cmd '%s' failed<br/>" % cmd
            shutil.move(fname, dest)

        return PAGE % args
    index.exposed = True

if __name__ == '__main__':
    cherrypy.server.socket_host = ADDR
    cherrypy.quickstart(GetYoutube())

