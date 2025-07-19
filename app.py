from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///pos.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'capitalfibre')
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600

# Initialize extensions
db = SQLAlchemy(app)  # Only SQLAlchemy instance
migrate = Migrate(app, db)
jwt = JWTManager(app)

# Register blueprints
from auth import auth_bp
from users import users_bp
from customers import customers_bp
from tickets import tickets_bp

app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)
app.register_blueprint(customers_bp)
app.register_blueprint(tickets_bp)

if __name__ == '__main__':
    app.run(debug=True)