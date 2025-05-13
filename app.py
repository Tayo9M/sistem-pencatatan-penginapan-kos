import os
import logging
from datetime import datetime
from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "kuncirahasiacharlie")  # Using fallback for development
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Database configuration - MySQL untuk deployment
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    # Fallback untuk development
    database_url = "sqlite:///kos_management.db"
    # Untuk MySQL lokal bisa gunakan:
    # database_url = "mysql://username:password@localhost/kos_db"

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

# Initialize SQLAlchemy with the app
db = SQLAlchemy(model_class=Base)
db.init_app(app)
