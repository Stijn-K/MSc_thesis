from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import os
from dotenv import load_dotenv

load_dotenv()

_DB = os.getenv('DB')
_SERVER = os.getenv('SERVER', '127.0.0.1')

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = _DB
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

from src import routes