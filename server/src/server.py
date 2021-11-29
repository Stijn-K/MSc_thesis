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


@app.route('/login', methods=['GET'])
def login():
    user = db.get_user_by_credentials(request.args.get('username'), request.args.get('password'))
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


if __name__ == '__main__':
    app.run(debug=True, host=_SERVER, port=5000, ssl_context='adhoc')
