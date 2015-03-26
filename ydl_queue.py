'''
I need a threadsafe queue I can take snapshots of the contents. The normal
python Queue implentations don't support that and I don't want to play games
with emptying and refilling them to see the contents.
'''

import threading

class YdlQueue(object):
    '''
    A simple queue class with the extension of adding 'peek_all' which gives us
    a copy of the current state of the queue
    '''
    def __init__(self, max_size=None):
        '''
        basic constructor, making an internal queue and a lock
        '''
        #read/write would be good here. None in stdlib?!
        self.lock = threading.Lock()
        self.queue = []
        self.max_size = max_size


    def put(self, item):
        '''
        put item in the queue (in back). returns true if it worked
        '''
        with self.lock:
            if self.max_size is not None and len(self.queue) > self.max_size:
                return False
            self.queue.append(item)
        return True


    def get(self):
        '''
        get item from the queue (front)
        '''
        ret = None
        with self.lock:
            if len(self.queue):
                print "RETURNING ONE"
                ret = self.queue[0]
                self.queue = self.queue[1:]
        return ret


    def peek_all(self):
        '''
        get a copy of the queue
        '''
        ret = []
        with self.lock:
            ret = self.queue
        return ret

