from BaseHTTPServer import BaseHTTPRequestHandler
from StringIO import StringIO


class DumbHTTPRequestHandler(BaseHTTPRequestHandler):
    """A crippled BaseHTTPRequestHandler -- we only want it for its request-
    parsing logic.

    """
    def __init__(self, request):
        BaseHTTPRequestHandler.__init__(self, request, None, None)

    def setup(self):
        self.rfile = StringIO(self.request)

    def handle(self):
        self.raw_requestline = self.rfile.readline()
        if not self.raw_requestline:
            return
        if not self.parse_request(): # An error code has been sent, just exit
            return

    def finish(self):
        pass


class FakeSocket(StringIO):

    def makefile(self, *_args, **_kws):
        return self
