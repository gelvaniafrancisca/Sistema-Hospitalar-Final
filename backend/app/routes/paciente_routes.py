# app/routes/paciente_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Paciente, Consulta, Medico
from datetime import datetime

paciente_bp = Blueprint('pacientes', __name__, url_prefix='/api/pacientes')

# Rota de teste
@paciente_bp.route('/teste', methods=['GET'])
def teste_paciente():
    return jsonify({'message': 'Rota de pacientes funcionando!'}), 200

# Buscar paciente por user_id
@paciente_bp.route('/usuario/<int:user_id>', methods=['GET'])
@jwt_required()
def get_paciente_by_user(user_id):
    try:
        print(f"🔍 Buscando paciente com user_id: {user_id}")
        
        paciente = Paciente.query.filter_by(user_id=user_id).first()
        
        if not paciente:
            print(f"❌ Paciente não encontrado para user_id: {user_id}")
            return jsonify({'error': 'Paciente não encontrado'}), 404
        
        print(f"✅ Paciente encontrado: {paciente.nome}")
        
        # Buscar consultas do paciente
        consultas = Consulta.query.filter_by(paciente_id=paciente.id).all()
        
        return jsonify({
            'id': paciente.id,
            'nome': paciente.nome,
            'email': paciente.email,
            'telefone': paciente.telefone,
            'data_nascimento': paciente.data_nascimento.isoformat() if paciente.data_nascimento else None,
            'tipo_sanguineo': paciente.tipo_sanguineo,
            'genero': paciente.genero,
            'endereco': paciente.endereco,
            'alergias': paciente.alergias,
            'condicoes_cronicas': paciente.condicoes_cronicas,
            'avatar': paciente.avatar,
            'total_consultas': len(consultas)
        }), 200
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return jsonify({'error': str(e)}), 500