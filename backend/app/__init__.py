# app/__init__.py
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    
    # Configurações
    app.config['SECRET_KEY'] = 'medhistory-super-secret-key-2024'
    app.config['JWT_SECRET_KEY'] = 'jwt-super-secret-key-2024'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/medhistory_ao'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
    
    # Inicializar extensões
    CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"])
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    
    # Registrar blueprints
    from app.routes.medico_routes import medico_bp
    app.register_blueprint(medico_bp)
    
    return app