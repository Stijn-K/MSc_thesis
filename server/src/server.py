from flask import Flask, request, make_response, render_template, redirect
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
        return make_response(render_template('login.html'))

    elif request.method == 'POST':
        user = db.get_user_by_credentials(request.json['username'], request.json['password'])

        if not user:
            return '', 401

        fingerprint = request.json['fingerprint']
        fingerprint['user-agent'] = request.headers.get('User-Agent')

        cookie = cookie_helper.generate_cookie(user, fingerprint=fingerprint)

        response = make_response(redirect('/user'))
        response.set_cookie('session_cookie', cookie)

        return response


@app.route('/user', methods=['GET', 'POST'])
def user():
    if request.method == 'GET':
        return render_template('user/user.html')

    elif request.method == 'POST':
        cookie = request.cookies.get('session_cookie')
        fingerprint = request.json
        fingerprint['user-agent'] = request.headers.get('User-Agent')

        success, result = cookie_helper.verify_cookie(cookie, fingerprint=fingerprint)

        template = render_template('user/user_body.html', success=success, result=result)
        return template


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


if __name__ == '__main__':
    app.run(debug=True, host=_SERVER, port=5000, ssl_context='adhoc')