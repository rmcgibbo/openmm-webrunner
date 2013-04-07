##############################################################################
# Imports
##############################################################################

# stdlib
import os
import base64
from threading import Lock
import time
import json

# tornado
from tornado import ioloop
from tornado.web import RequestHandler, Application
from tornado.websocket import WebSocketHandler

# mine
from lib.validation import validate_openmm
from lib.executor import with_timeout

##############################################################################
# GLOBALS
##############################################################################

APP_SECRET = os.environ.get('APP_SECRET', '')

# should be a database
REQUESTS = {}

##############################################################################
# Classes
##############################################################################


class NotifyHandler(RequestHandler):
    def post(self):
        if self.get_argument('app_secret') != APP_SECRET:
            print 'app secret is not right'
            return

        request_id = self.get_argument('request_id', None)
        if request_id is None:
            return
        
        print 'recieved post notify', request_id
        # record the request_id as a good one
        REQUESTS[request_id] = time.time()

    def get(self):
        print 'Recieved a get request'
        self.write('Hello world')

class RunHandler(WebSocketHandler):

    # we only want this to execute one proc at a time
    lock = Lock()
    # how long should we let clients execute for
    timeout = 30
    
    def on_message(self, packet):
        message = json.loads(packet)

        if message.get('request_id', None) not in REQUESTS:
            print 'AUTH ERROR'
            print 'message', message.get('request_id')
            print 'requests', REQUESTS
            self.write_error('Sorry.')
            return

        got_lock = self.lock.acquire(0)
        if not got_lock:
            self.write_error("Sorry, I'm busy")
            return
        
        scriptcode = message.get('scriptcode', '')
        is_valid, validation_error = validate_openmm(scriptcode)

        if is_valid:
            files = message.get('files', [])
            timed_out = with_timeout(scriptcode, stdout_cb=self.write_output,
                                     stderr_cb=self.write_error, timeout=self.timeout,
                                     files=files)
            # print 'timed out', timed_out
            if timed_out:
                self.write_error('Your script timed out!')
        else:
            self.write_error(validation_error)
            
        self.lock.release()


    def write_output(self, message):
        # print 'output', message
        self.write_message(json.dumps({'stdout': message}))

    def write_error(self, message):
        # print 'error', message
        self.write_message(json.dumps({'stderr': message}))


application = Application([
        (r'/notify', NotifyHandler),
        (r'/run', RunHandler),
])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    application.listen(port)
    ioloop.IOLoop.instance().start()

