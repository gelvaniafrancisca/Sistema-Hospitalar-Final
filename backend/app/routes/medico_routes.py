# app/routes/medico_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Medico, User, Consulta, Paciente
from datetime import datetime

medico_bp = Blueprint('medicos', __name__, url_prefix='/api/medicos')

# Buscar médico por user_id
@medico_bp.route('/usuario/<int:user_id>', methods=['GET'])
@jwt_required()
def get_medico_by_user(user_id):
    medico = Medico.query.filter_by(user_id=user_id).first()
    if not medico:
        return jsonify({'error': 'Médico não encontrado'}), 404
    
    # Buscar consultas do médico
    consultas = Consulta.query.filter_by(medico_id=medico.id).all()
    pacientes_unicos = set()
    for c in consultas:
        pacientes_unicos.add(c.paciente_id)
    
    return jsonify({
        'id': medico.id,
        'nome': medico.nome,
        'email': medico.email,
        'telefone': medico.telefone,
        'registro_oma': medico.registro_oma,
        'especialidade': medico.especialidade,
        'avatar': medico.avatar,
        'total_pacientes': len(pacientes_unicos),
        'total_consultas': len(consultas),
        'experiencia': medico.experiencia,
        'formacao': medico.formacao,
        'rating': 4.8
    }), 200

# Buscar consultas de hoje do médico
@medico_bp.route('/<int:medico_id>/consultas/hoje', methods=['GET'])
@jwt_required()
def get_consultas_hoje(medico_id):
    hoje = datetime.now().date()
    consultas = Consulta.query.filter_by(
        medico_id=medico_id,
        data=hoje
    ).order_by(Consulta.hora).all()
    
    result = []
    for c in consultas:
        paciente = Paciente.query.get(c.paciente_id)
        result.append({
            'id': c.id,
            'paciente_id': c.paciente_id,
            'paciente_nome': paciente.nome if paciente else None,
            'paciente_avatar': paciente.avatar if paciente else None,
            'hora': c.hora.strftime('%H:%M'),
            'duracao': c.duracao,
            'tipo': c.tipo,
            'status': c.status,
            'motivo': c.motivo,
            'observacoes': c.observacoes,
            'link_teleconsulta': c.link_teleconsulta
        })
    
    return jsonify(result), 200

# Atualizar médico
@medico_bp.route('/<int:medico_id>', methods=['PUT'])
@jwt_required()
def atualizar_medico(medico_id):
    data = request.get_json()
    medico = Medico.query.get_or_404(medico_id)
    
    if 'nome' in data:
        medico.nome = data['nome']
    if 'email' in data:
        medico.email = data['email']
    if 'telefone' in data:
        medico.telefone = data['telefone']
    if 'especialidade' in data:
        medico.especialidade = data['especialidade']
    if 'registro_oma' in data:
        medico.registro_oma = data['registro_oma']
    if 'formacao' in data:
        medico.formacao = data['formacao']
    if 'experiencia' in data:
        medico.experiencia = data['experiencia']
    
    db.session.commit()
    
    return jsonify({'message': 'Médico atualizado com sucesso'}), 200