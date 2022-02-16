from flask import Flask, request, make_response, jsonify, render_template, redirect
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

        cookie = cookie_helper.generate_cookie(user)

        response = make_response(render_template('login.html', logged_in=True))
        response.set_cookie('session_cookie', cookie)

        return response


@app.route('/user', methods=['GET'])
def user():
    cookie = request.cookies.get('session_cookie')
    success, result = cookie_helper.verify_cookie(cookie)

    response = make_response(render_template('user.html', success=success, result=result))

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


if __name__ == '__main__':
    app.run(host=_SERVER, port=5000, ssl_context='adhoc')
