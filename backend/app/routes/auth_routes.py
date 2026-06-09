# app/routes/auth_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app.models import db, User, Paciente, Medico
from flask_bcrypt import Bcrypt
import re

bcrypt = Bcrypt()
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    print(f"Dados recebidos: {data}")  # Debug
    
    if not data.get('email') or not data.get('password') or not data.get('nome'):
        return jsonify({'error': 'Email, nome e senha são obrigatórios'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email já cadastrado'}), 400
    
    password_hash = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    user = User(
        email=data['email'],
        password_hash=password_hash,
        user_type='paciente',
        is_active=True
    )
    db.session.add(user)
    db.session.flush()
    
    paciente = Paciente(
        user_id=user.id,
        nome=data['nome'],
        email=data['email'],
        telefone=data.get('telefone', ''),
        tipo_sanguineo=data.get('tipo_sanguineo'),
        avatar=data['nome'][0].upper() + (data['nome'].split(' ')[1][0].upper() if len(data['nome'].split(' ')) > 1 else '')
    )
    db.session.add(paciente)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Conta criada com sucesso!',
        'user_id': user.id,
        'paciente_id': paciente.id
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not bcrypt.check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Email ou senha inválidos'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Conta desativada'}), 403
    
    nome = ''
    avatar = ''
    
    if user.user_type == 'paciente':
        paciente = Paciente.query.filter_by(user_id=user.id).first()
        if paciente:
            nome = paciente.nome
            avatar = paciente.avatar
    elif user.user_type == 'medico':
        medico = Medico.query.filter_by(user_id=user.id).first()
        if medico:
            nome = medico.nome
            avatar = medico.avatar
    else:
        nome = 'Administrador'
        avatar = 'AD'
    
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            'user_type': user.user_type,
            'email': user.email,
            'nome': nome,
            'avatar': avatar
        }
    )
    
    return jsonify({
        'access_token': access_token,
        'token_type': 'bearer',
        'user_type': user.user_type,
        'user_id': user.id,
        'nome': nome,
        'email': user.email,
        'avatar': avatar
    }), 200