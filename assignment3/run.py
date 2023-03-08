#!venv/bin/python
from app import webapp
import logging

logging.basicConfig(filename='access.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
logging.warning('This will get logged to a file')
#webapp.run(host='0.0.0.0',debug=True)