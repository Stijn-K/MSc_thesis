from flask import Flask, request, make_response, render_template, g
import db_helpers as db
import cookie as cookie_helper
import os
import time

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
_SERVER = os.getenv('SERVER', 'localhost')
_PORT = 5000


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

        cid, n_s, k_s, t_s, ticket = cookie_helper.generate_otc(user)

        response = make_response(render_template('login.html', logged_in=True))
        response.headers['X-OTC-SET'] = f'{cid},{_SERVER}:{_PORT},/,{n_s},{k_s},{t_s},{ticket}'

        return response


@app.route('/user', methods=['GET'])
def user():
    try:
        success, result = cookie_helper.verify_otc(*request.headers['X-OTC'].split(','), request.url, '')
    except (KeyError, TypeError, ValueError):
        success = False
        result = 'Endpoint requires OTC'

    response = make_response(render_template('user.html', success=success, result=result))
    return response


@app.before_first_request
def initialize():
    app.logger.info('Initializing server...')
    app.logger.info('Initializing DB...')
    db.initialize_db()
    cookie_helper.initialize_otc()


@app.before_request
def before_request():
    g.start_time = time.perf_counter_ns()


@app.after_request
def set_headers(response):
    # get elapsed time in nanoseconds and add to response headers
    total_time = time.perf_counter_ns() - g.start_time
    response.headers['request_time'] = total_time

    # disable caching and set headers for CORS
    response.cache_control.no_store = True
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST'
    return response


if __name__ == '__main__':
    app.run(debug=True, host=_SERVER, port=_PORT, ssl_context='adhoc')
