from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app, supports_credentials=True)

# Config
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret')  # replace in prod

# Extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Import and register blueprints
from routes.users import users_bp
from routes.service_plans import service_plans_bp
from routes.subscriptions import subscriptions_bp
from routes.payments import payments_bp
from routes.equipment import equipment_bp
from routes.network_nodes import network_nodes_bp
from routes.dashboard import dashboard_bp

app.register_blueprint(users_bp)
app.register_blueprint(service_plans_bp)
app.register_blueprint(subscriptions_bp)
app.register_blueprint(payments_bp)
app.register_blueprint(equipment_bp)
app.register_blueprint(network_nodes_bp)
app.register_blueprint(dashboard_bp)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
