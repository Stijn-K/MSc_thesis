from flask import Flask, request, make_response, render_template, redirect

import werkzeug.serving
import ssl
import OpenSSL

import db_helpers as db
import cookie as cookie_helper
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
_SERVER = os.getenv('SERVER', 'localhost')


@app.route('/', methods=['GET'])
@app.route('/alive', methods=['GET'])
def alive():
    return make_response(render_template('alive.html'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return make_response(render_template('login.html', logged_in=False))

    elif request.method == 'POST':
        user = db.get_user_by_credentials(request.form['username'], request.form['password'])

        if not user:
            return make_response(render_template('login.html', logged_in=False, error='Invalid credentials'))

        cert: OpenSSL.crypto.X509 = request.environ['peercert']

        cookie = cookie_helper.generate_cookie(user, cert)

        print(cookie)

        response = make_response(render_template('login.html', logged_in=True))
        response.set_cookie('session_cookie', cookie)

        return response


@app.route('/user', methods=['GET'])
def user():
    cookie = request.cookies.get('session_cookie')
    cert: OpenSSL.crypto.X509 = request.environ['peercert']

    success, result = cookie_helper.verify_cookie(cookie, cert)

    response = make_response(render_template('user.html', success=success, result=result))

    return response


@app.before_first_request
def initialize():
    app.logger.info('Initializing server...')
    app.logger.info('Initializing DB...')
    db.initialize_db()
    cookie_helper.initialize_obc()


@app.after_request
def set_headers(response):
    response.cache_control.no_store = True
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST'
    return response


class PeerCertWSGIRequestHandler(werkzeug.serving.WSGIRequestHandler):
    def make_environ(self):
        environ = super(PeerCertWSGIRequestHandler, self).make_environ()
        x509_binary = self.connection.getpeercert(True)
        x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, x509_binary)
        environ['peercert'] = x509
        return environ


app_key = '../certs/server.key'
app_pw = None
app_cert = '../certs/server.crt'

ca_cert = '../certs/ClientCA.pem'

ssl_context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH, cafile=ca_cert)

ssl_context.load_cert_chain(certfile=app_cert, keyfile=app_key, password=app_pw)
ssl_context.verify_mode = ssl.CERT_REQUIRED


if __name__ == '__main__':
    app.run(
            debug=True,
            host=_SERVER,
            port=5000,
            request_handler=PeerCertWSGIRequestHandler,
            ssl_context=ssl_context,
            )
