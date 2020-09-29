from flask import Flask,session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from config import Config

UPLOAD_FOLDER = './file/'
FILENAME_IMPORT = 'import_data.json'
ALLOWED_EXTENSIONS = {'json'}

app = Flask(__name__)
app.debug = True
app.config.from_object(Config)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['FILENAME_IMPORT'] = FILENAME_IMPORT
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024

# app.run(host="127.0.0.1", port=8000)
db = SQLAlchemy(app)
migrate = Migrate(app, db)




from app import routes, models