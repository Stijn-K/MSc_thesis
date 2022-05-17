from flask import request, make_response, render_template, g
import src.db_helpers as db
import src.cookie as cookie_helper
import time

from src import app

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
            return make_response(render_template('login.html', logged_in=False, error='Invalid credentials'))

        fingerprint = request.json['fingerprint']
        fingerprint['user-agent'] = request.headers.get('User-Agent')

        cookie = cookie_helper.generate_cookie(user, fingerprint=fingerprint)

        response = make_response(render_template('login.html', logged_in=True))
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

        return render_template('user/user_body.html', success=success, result=result)


@app.before_first_request
def initialize():
    app.logger.info('Initializing server...')
    app.logger.info('Initializing DB...')
    db.initialize_db()


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
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST'
    return response
