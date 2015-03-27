'''
Various utility functions that have nowhere else to live
'''

import os
import sys
import datetime
import ConfigParser

class YdlException(Exception):
    'exception type for this project'
    

SUFFIXES = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
def humansize(nbytes):
    'taken from stackoverflow' 
    if nbytes == 0:
        return '0 B'
    i = 0
    while nbytes >= 1024 and i < len(SUFFIXES)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, SUFFIXES[i])


def date_from_unix(unix_ts):
    'give back human readable from unix eopch time'
    dtm = datetime.datetime.fromtimestamp(unix_ts)
    return dtm.strftime('%Y-%m-%d %H:%M:%S')


def text_to_html(ret):
    'turn \n into <br/> and make sure one is on the end'
    ret['text'] = ret['text'].replace('\n', '<br/>')
    if not ret['text'].endswith('<br/>'):
        ret['text'] = ret['text'] + '<br/>'
    return ret


def name_to_path(name):
    'make sure a artist/title name can be used in a UNIX path'
    return name.replace(os.path.sep, '_')


def get_config():
    'get a config object from sys.argv[1]'
    if len(sys.argv) < 2:
        raise YdlException("You need to pass a config file as the first argument!")
        
    config = ConfigParser.ConfigParser()
    config.read(sys.argv[1])
    return config

