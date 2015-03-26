#!/usr/bin/env python

'''
Script to download youtube videos and organize them (if possible).
'''

import cherrypy
from cherrypy.process.plugins import Monitor

#from pyechonest import song, artist

from youtubedl_wrapper import YoutubeDlWrapper, YoutubeDlWrapperException
from ydl_queue import YdlQueue

DOWNLOAD_DIR = "video/"
ADDR = '0.0.0.0'
PAGE = '''
<HTML>
    <TITLE>Download Youtube Videos</TITLE>
    <BODY>
        <meta http-equiv="refresh" content="5"/>
        <CENTER><H2>Download Youtube Videos</H2></CENTER>
        <FORM name="input" action="" method="post">
            <CENTER>
                Enter YouTube URL to download: <input type="text" name="url"/>
                <BR/>
                <input type="submit" value="Submit">
                <BR/>
            </CENTER>
        </FORM>
        <CENTER>
        %(text)s
        </CENTER>
    </BODY>
</HTML>
'''

YDL_QUEUE = YdlQueue()
DOWN_QUEUE = YdlQueue()
TITLE_QUEUE = YdlQueue()
ERR_QUEUE = YdlQueue()
RECENT_QUEUE = YdlQueue()


def title_worker():
    '''
    resolve titles for videos in TITLE_QUEUE
    '''
    while True:
        ydw = TITLE_QUEUE.get()
        if ydw == None:
            return
        YDL_QUEUE.put(ydw)
        ret = ydw.get_title()
        if ret['err']:
            ERR_QUEUE.put(ret['text'])


def download_worker():
    '''
    Download videos in DOWN_QUEUE
    '''
    ydw = YDL_QUEUE.get()
    if ydw == None:
        return
    DOWN_QUEUE.put(ydw)
    ret = fix_text(ydw.download())
    if ret['err']:
        ERR_QUEUE.put(ret['text'])
    DOWN_QUEUE.remove(ydw)
    RECENT_QUEUE.put(ydw)


def queue_to_table(queue, title, link=None, reverse=False):
    '''
    get a table from a queue
    '''
    entries = queue.peek_all()
    if len(entries) == 0:
        return ''
    ret = '<table style="width:100%%" border=1>'
    if link:
        ret += '<tr><td><center><b>%s</b><a href="%s"> ' \
               '(clear)</a></center></td></tr>' % (title, link)
    else:
        ret += '<tr><td><b>%s</b></td></tr>' % title
    if reverse:
        entries.reverse()
    for entry in entries:
        ret += '<tr><td>%s</td></tr>' % str(entry)
    ret += '</table><br/>'
    return ret


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
            ydw = None
            try:
                ydw = YoutubeDlWrapper(url)
            except YoutubeDlWrapperException, exc:
                ERR_QUEUE.put(str(exc))
                url = None
            if url:
                TITLE_QUEUE.put(ydw)
        args['text'] += queue_to_table(DOWN_QUEUE, 'Downloading')
        args['text'] += queue_to_table(YDL_QUEUE, 'Queue')
        args['text'] += queue_to_table(ERR_QUEUE, 'Errors', 'clear_errors')
        args['text'] += queue_to_table(TITLE_QUEUE, 'Waiting for titles')
        RECENT_QUEUE.drop_lru(10)
        args['text'] += queue_to_table(RECENT_QUEUE, 'Recently Downloaded',
            None, True)

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
    Monitor(cherrypy.engine, title_worker, frequency=1).subscribe()
    Monitor(cherrypy.engine, download_worker, frequency=1).subscribe()
    cherrypy.quickstart(GetYoutube())


if __name__ == '__main__':
    main()

