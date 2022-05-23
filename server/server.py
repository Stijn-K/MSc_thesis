import os
from dotenv import load_dotenv

from src import app

load_dotenv()

_SERVER = os.getenv("SERVER")

if __name__ == '__main__':
    app.run(host=_SERVER, port=5000, ssl_context='adhoc', debug=True)
