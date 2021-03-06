'''
A wrapper around youtube-dl binary
'''

import os
import shutil
from subprocess import Popen, PIPE

def get_proc(cmd):
    'just got tired of typing this'
    return Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                 close_fds=True)

class YoutubeDlWrapperException(Exception):
    '''
    custom exception type
    '''

class YoutubeDlWrapper(object):
    '''
    A simple wrapper around youtube-dl binary.
    '''
    def __init__(self, url):
        '''
        Save off URL for later use
        '''
        if not url.startswith('http://') and not url.startswith('https://'):
            raise YoutubeDlWrapperException("Bad URL: %s" % url)
        self.url = url
        self.title = None

    def __str__(self):
        'stringify'
        if self.title:
            return self.title
        return self.url


    @staticmethod
    def _run(cmd):
        '''
        Run and return a dict indicating any errors and the text output.
        Keys: err, text
        '''
        ret = {'err':False}
        proc = get_proc(cmd)
        (stdout, stderr) = proc.communicate()
        if proc.returncode == 0:
            ret['text'] = stdout
        else:
            ret['err'] = True
            ret['text'] = ''
            if stderr != '':
                ret['text'] += "%s\n" % stderr
            elif stdout != '':
                ret['text'] += "%s\n" % stdout
            else: #unlikely....
                ret['text'] += "no output, only got return code: %d" % \
                    proc.returncode

        return ret


    def get_title(self):
        '''
        Get title of the video from the URL
        '''
        if self.title:
            return {'err':False, 'text':self.title}
        cmd = 'youtube-dl --get-title %s' % self.url
        ret = self._run(cmd)
        if not ret['err']:
            self.title = ret['text']
        return self._run(cmd)


    def get_filename(self):
        '''
        Get filename of the video from the URL
        '''
        cmd = 'youtube-dl --get-filename %s' % self.url
        return self._run(cmd)


    def download(self, cfg):
        '''
        Download the video and rename/move it
        '''
        ret = self.get_title()
        if ret['err']:
            return ret
        title = ret['text'].strip()


        ret = self.get_filename()
        if ret['err']:
            return ret
        fname = ret['text'].strip()
        ext = fname.split('.')[-1]
        downdir = os.path.expanduser(cfg.get('GetYoutube', 'DownloadDirectory'))
        dest = os.path.join(downdir, title)
        dest = dest + '.' + ext
        if os.path.exists(dest):
            ret = {'err': True}
            ret['text'] = "ERROR the file '%s' already exists" % dest
            return ret

        cmd = 'youtube-dl %s' % self.url
        ret = self._run(cmd)
        if not ret['err']:
            ret['text'] += '\nOk, downloaded to %s' % dest
            shutil.move(fname, dest)
        return ret


