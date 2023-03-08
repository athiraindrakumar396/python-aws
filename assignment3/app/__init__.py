
from flask import Flask

webapp = Flask(__name__)

from app import config
from app import main