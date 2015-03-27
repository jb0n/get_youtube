#!/usr/bin/env python

'''
Script to download youtube videos and organize them (if possible).
'''

import os
import shutil
import urllib

import cherrypy
from cherrypy.process.plugins import Monitor

from pyechonest import song, artist

from youtubedl_wrapper import YoutubeDlWrapper, YoutubeDlWrapperException
from ydl_queue import YdlQueue
from ydl_util import humansize, date_from_unix, text_to_html, name_to_path

DOWNLOAD_DIR = "video/"
ADDR = '0.0.0.0'

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
    ret = text_to_html(ydw.download())
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


class GetYoutube(object):
    'The webserver class to downlod videos from youtube'
    page_header = '''
        <TABLE style="width:100%%" align="center">
          <TR>
            <TD align="center"><a href="/">Download</a></TD>
            <TD align="center"><a href="/manage">Manage</a></TD>
            <TD align="center"><a href="/settings">Settings</a></TD>
          </TR>
        </TABLE>
        <HR/>
    '''
    index_page = '''
    <HTML>
      <TITLE>Download Youtube Videos</TITLE>
      <BODY>
        <meta http-equiv="refresh" content="5"/>
        <CENTER><H2>Download Youtube Videos</H2></CENTER>
        %s 
        <FORM name="input" action="" method="post">
          <CENTER>
            Enter YouTube URL to download: <input type="text" name="url"/>
            <BR/>
            <input type="submit" value="Submit">
            <BR/>
          </CENTER>
        </FORM>
          <CENTER>
          %%(text)s
          </CENTER>
      </BODY>
    </HTML>
    ''' % page_header
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
        return self.index_page % args
    index.exposed = True


    def clear_errors(self):
        '''
        clear error queue
        '''
        ERR_QUEUE.clear()
        raise cherrypy.HTTPRedirect("/")
    clear_errors.exposed = True


    manage_page = '''
    <HTML>
      <TITLE>Manage Videos</TITLE>
      <BODY>
        <CENTER>
          <H2>Manage Videos</H2>
          %s
        </CENTER>
        %%(text)s
      </BODY>
    </HTML>
    ''' % page_header
    def manage(self, filename=None):
        '''
        '''
        args = {'text':''}
        if filename == None:
            all_files = os.listdir(DOWNLOAD_DIR)
            all_files.sort()
            for fname in all_files:
                args['text'] += '<ul><a href="?filename=%s">%s</a></ul>' % \
                    (urllib.quote(fname), fname)
        else:
            fname = os.path.join(DOWNLOAD_DIR, filename)
            fname = os.path.normpath(fname)
            if not fname.startswith(DOWNLOAD_DIR):
                args['text'] += "Bad filename %s. File outside of download dir '%s'" % \
                    (filename, DOWNLOAD_DIR)
                return self.manage_page % args
            fstats = os.stat(fname)
            targs = {
                'filename': filename,
                'quoted_filename': urllib.quote(filename),
                'size': humansize(fstats.st_size),
                'creation_date': date_from_unix(fstats.st_ctime),
                'last_accessed': date_from_unix(fstats.st_atime)
            }
            args['text'] += '''
            <CENTER>
              <TABLE>
                <TR><H3>%(filename)s</H3></TR>
                <TR><TD>size:</TD><TD>%(size)s</TD>
                <TR><TD>creation date:</TD><TD>%(creation_date)s</TD>
                <TR><TD>last accessed:</TD><TD>%(last_accessed)s</TD>
                <TR><TD>
                  <FORM name="classify_form" action="classify" method="post">
                    <INPUT type="hidden" name="filename" value="%(quoted_filename)s"/>
                    <INPUT type="submit" value="Classify"/>
                  </FORM>
                </TD>
                <TD>
                  <FORM name="delete_form" action="delete" method="post">
                    <INPUT type="hidden" name="filename" value="%(quoted_filename)s"/>
                    <INPUT type="submit" value="Delete"/>
                  </FORM>
                </TD></TR>
              </TABLE>
            </CENTER>
            ''' % targs
        return self.manage_page % args
    manage.exposed = True

    delete_page = '''
    <HTML>
      <TITLE>Delete File</TITLE>
      <BODY>
        <CENTER>
          <H2>Delete File</H2>
          %s
        %%(text)s
        </CENTER>
      </BODY>
    </HTML>
    ''' % page_header
    def delete(self, filename, really_delete=None):
        '''
        delete a file
        '''
        quoted_filename = filename
        filename = urllib.unquote(filename)
        args = {'text':''}
        if really_delete:
            fname = os.path.join(DOWNLOAD_DIR, filename)
            fname = os.path.normpath(fname)
            if not fname.startswith(DOWNLOAD_DIR):
                args['text'] += "Bad filename %s. File outside of download dir '%s'" % \
                    (filename, DOWNLOAD_DIR)
                return self.delete_page % args
            os.unlink(fname)
            args['text'] = 'Ok, deleted<BR/>%s' % filename
            return self.delete_page % args

        targs = {'filename': filename,
                 'quoted_filename': quoted_filename
        }
        args['text'] = '''<H3>Are you sure you want to delete?</H3><BR/> %(filename)s
        <FORM name="delete_form" action="delete" method="post">
          <INPUT type="hidden" name="filename" value="%(quoted_filename)s"/>
          <INPUT type="hidden" name="really_delete" value=1/>
          <INPUT type="submit" value="Delete"/>
        </FORUM>
        ''' % targs
        return self.delete_page % args
    delete.exposed = True 


    classify_page = '''
    <HTML>
      <TITLE>Classify File</TITLE>
      <BODY>
        <CENTER>
          <H2>Classify File</H2>
          %s
        %%(text)s
        </CENTER>
      </BODY>
    </HTML>
    ''' % page_header
    def classify(self, filename, new_name=None):
        '''
        classify a file
        '''
        filename = urllib.unquote(filename)
        quoted_filename = filename
        args = {'text':''}
        targs = {'filename': filename,
                 'quoted_filename': quoted_filename
        }

        if new_name:
            ext = filename.split('.')[-1]
            new_name = urllib.unquote(new_name)
            artist, title = new_name.split(os.path.sep)
            destdir = os.path.join(DOWNLOAD_DIR, artist)
            if os.path.exists(destdir):
                if not os.path.isdir(destdir):
                    args['text'] += "Cannot make '%s', since the path exists and isn't a file!" % \
                        artist
                    return self.classify_page % args
            else:
                os.mkdir(destdir)
            srcfile = os.path.join(DOWNLOAD_DIR, filename)
            dstfile = os.path.join(destdir, title) + '.' + ext
            shutil.move(srcfile, dstfile)
            args['text'] += 'Ok, moved %s to %s' % (srcfile, dstfile)
            return self.classify_page % args


        results = song.search(combined=filename)
        args['text'] += '<H3>Filename:</H3>%s<BR/><BR/><TABLE>' % filename
        args['text'] += '<TABLE><TR><TD/><TD><B>Artist</B></TD><TD><B>Title</B></TD>'
        args['text'] += '<FORM name="classify_form" action="classify" method="post">'
        args['text'] += '<INPUT type="hidden" name="filename" value="%(filename)s"/>' % targs

        for res in results:
            artist = name_to_path(res.artist_name)
            title = name_to_path(res.title)
            targs['artist'] = res.artist_name
            targs['title'] = res.title
            new_name = os.path.join(urllib.quote(artist), urllib.quote(title))
            targs['new_name'] = new_name
            args['text'] += '''
              <TR>
                <TD><INPUT type="radio" name="new_name" value="%(new_name)s"></TD>
                <TD>%(artist)s</TD>
                <TD>%(title)s</TD>
            ''' % targs
        args['text'] += '<INPUT type="submit" value="Classify"/>'
        args['text'] += '</FORM></TABLE>'

        return self.classify_page % args
    classify.exposed = True


    settings_page = '''
    <HTML>
      <TITLE>Settings</TITLE>
      <BODY>
        <CENTER>
          <H2>Settings</H2>
          %s
          %%(text)s
        </CENTER>
      </BODY>
    </HTML>
    ''' % page_header
    def settings(self):
        '''
        Manage configuration/settings
        '''
        args = {'text':''}
        return self.settings_page % args
    settings.exposed = True


def main():
    'do ALL the things'
    cherrypy.server.socket_host = ADDR
    Monitor(cherrypy.engine, title_worker, frequency=1).subscribe()
    Monitor(cherrypy.engine, download_worker, frequency=1).subscribe()
    cherrypy.quickstart(GetYoutube())


if __name__ == '__main__':
    main()

