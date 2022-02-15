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
    return make_response(render_template('alive.html', client_cert=request.environ))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return make_response(render_template('login.html'))

    elif request.method == 'POST':
        user = db.get_user_by_credentials(request.form['username'], request.form['password'])

        if not user:
            return '', 401

        cookie = cookie_helper.generate_cookie(user)

        response = make_response(redirect('/user'))
        response.set_cookie('session_cookie', cookie)

        return response


@app.route('/user', methods=['GET'])
def user():
    cookie = request.cookies.get('session_cookie')
    user = cookie_helper.verify_cookie(cookie)
    try:
        username = user['username']
    except (TypeError, KeyError):
        username = None

    response = make_response(render_template('user.html', username=username, cookie=cookie))
    return response


@app.before_first_request
def initialize():
    app.logger.info('Initializing server...')
    app.logger.info('Initializing DB...')
    db.initialize_db()


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
        print(x509_binary)
        if x509_binary:
            x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, x509_binary)
            environ['peercert'] = x509
        return environ

ssl_context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
# ssl_context = ssl.SSLContext()

app_key = '../certs/server.key'
app_cert = '../certs/server.crt'

ssl_context.load_cert_chain(certfile=app_cert, keyfile=app_key, password=None)
ssl_context.verify_mode = ssl.CERT_REQUIRED


if __name__ == '__main__':
    app.run(
            debug=True,
            host=_SERVER,
            port=5000,
            request_handler=PeerCertWSGIRequestHandler,
            ssl_context=ssl_context,
            )
