import OpenSSL
import werkzeug.serving
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
    return '', 204


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        username = request.args.get('username')
        password = request.args.get('password')
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

    user = db.get_user_by_credentials(username, password)

    if not user:
        return '', 401

    cookie = cookie_helper.generate_cookie(user)

    response = make_response()
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


@app.route('/test', methods=['POST'])
def test():
    data = request.data
    print(data)
    print(request.cookies)
    print(request.environ['HTTP_USER_AGENT'])
    return '', 200


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
    app.run(debug=True,
            host=_SERVER,
            port=5000,
            ssl_context='adhoc')
