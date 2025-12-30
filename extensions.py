from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialize extensions here (without app)
db = SQLAlchemy()
login_manager = LoginManager()