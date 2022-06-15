import werkzeug.serving
import ssl
import OpenSSL

from src import app

import os
from dotenv import load_dotenv

load_dotenv()

_SERVER = os.getenv("SERVER")


class PeerCertWSGIRequestHandler(werkzeug.serving.WSGIRequestHandler):
    def make_environ(self):
        environ = super(PeerCertWSGIRequestHandler, self).make_environ()
        x509_binary = self.connection.getpeercert(True)
        x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, x509_binary)
        environ['peercert'] = x509
        return environ


app_key = 'certs/server.key'
app_pw = None
app_cert = 'certs/server.crt'

ca_cert = 'certs/ClientCA.pem'

ssl_context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH, cafile=ca_cert)

ssl_context.load_cert_chain(certfile=app_cert, keyfile=app_key, password=app_pw)
ssl_context.verify_mode = ssl.CERT_REQUIRED


if __name__ == '__main__':
    app.run(
            debug=False,
            host=_SERVER,
            port=5000,
            request_handler=PeerCertWSGIRequestHandler,
            ssl_context=ssl_context,
            )