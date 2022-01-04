from flask import Flask, request, make_response, render_template, redirect
import db_helpers as db
import cookie as cookie_helper
import os
import json

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
        challenges = json.dumps(cookie_helper.generate_challenges())
        return make_response(render_template('login.html', challenges=challenges))

    elif request.method == 'POST':
        user = db.get_user_by_credentials(request.json['username'], request.json['password'])

        if not user:
            return '', 401

        cookie = cookie_helper.generate_cookie(user, challenges=request.json['challenges'])

        response = make_response(redirect('/user'))
        response.set_cookie('session_cookie', cookie)

        return response


@app.route('/user', methods=['GET', 'POST'])
def user():
    cookie = request.cookies.get('session_cookie')
    if not cookie:
        return redirect('/login')

    user = db.get_user_by_cookie(cookie)

    if request.method == 'GET':
        challenge = cookie_helper.get_challenge(user['id'])
        if not challenge:
            return 'Oops! no more challenges to give out', 401

        return render_template('user/user.html', challenges=[challenge])

    elif request.method == 'POST':
        crs = list(request.json.items())[0]
        success, result = cookie_helper.verify_cookie(cookie, challenge_response=crs)
        return render_template('user/user_body.html', success=success, result=result)


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
