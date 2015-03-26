'''
A wrapper around youtube-dl binary
'''

import os
import shutil
from subprocess import Popen, PIPE

DOWNLOAD_DIR = "video/"

def get_proc(cmd):
    'just got tired of typing this'
    return Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                 close_fds=True)

class YoutubeDlWrapper(object):
    '''
    A simple wrapper around youtube-dl binary.
    '''
    def __init__(self, url):
        '''
        Save off URL for later use
        '''
        self.url = url
        self.title = None


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
            ret['text'] = "ERROR RETURN FROM youtube-dl binary:\n" \
            "stdout: %s\nstderr: %s" % (stdout, stderr)
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


    def download(self):
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

        dest = os.path.join(DOWNLOAD_DIR, title)
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


