# app/routes/consulta_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Consulta, Paciente, Medico, User
from datetime import datetime
import traceback

consulta_bp = Blueprint('consultas', __name__, url_prefix='/api/consultas')

# Listar todas as consultas (GET)
@consulta_bp.route('/', methods=['GET', 'OPTIONS'])
@jwt_required()
def listar_consultas():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        consultas = Consulta.query.order_by(Consulta.data.desc()).all()
        result = []
        
        for c in consultas:
            paciente = Paciente.query.get(c.paciente_id)
            medico = Medico.query.get(c.medico_id)
            
            result.append({
                'id': c.id,
                'paciente_id': c.paciente_id,
                'paciente_nome': paciente.nome if paciente else 'Desconhecido',
                'medico_id': c.medico_id,
                'medico_nome': medico.nome if medico else 'Desconhecido',
                'especialidade': medico.especialidade if medico else '',
                'data': c.data.isoformat(),
                'hora': c.hora.strftime('%H:%M'),
                'duracao': c.duracao,
                'tipo': c.tipo,
                'status': c.status,
                'motivo': c.motivo or '',
                'observacoes': c.observacoes or '',
                'link_teleconsulta': c.link_teleconsulta or ''
            })
        
        return jsonify(result), 200
    except Exception as e:
        print(f"❌ Erro ao listar consultas: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Criar nova consulta (POST)
@consulta_bp.route('/', methods=['POST', 'OPTIONS'])
@jwt_required()
def criar_consulta():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        if not data.get('paciente_id') or not data.get('medico_id'):
            return jsonify({'error': 'Paciente e médico são obrigatórios'}), 400
        
        paciente = Paciente.query.get(data['paciente_id'])
        if not paciente:
            return jsonify({'error': 'Paciente não encontrado'}), 404
        
        medico = Medico.query.get(data['medico_id'])
        if not medico:
            return jsonify({'error': 'Médico não encontrado'}), 404
        
        data_consulta = datetime.strptime(data['data'], '%Y-%m-%d').date()
        hora_consulta = datetime.strptime(data['hora'], '%H:%M').time()
        
        # Verificar conflito de horário
        consulta_existente = Consulta.query.filter_by(
            medico_id=data['medico_id'],
            data=data_consulta,
            hora=hora_consulta
        ).first()
        
        if consulta_existente:
            return jsonify({'error': 'Médico já possui consulta neste horário'}), 400
        
        nova_consulta = Consulta(
            paciente_id=data['paciente_id'],
            medico_id=data['medico_id'],
            data=data_consulta,
            hora=hora_consulta,
            tipo=data.get('tipo', 'presencial'),
            motivo=data.get('motivo', ''),
            duracao=data.get('duracao', 30),
            status='agendada'
        )
        
        db.session.add(nova_consulta)
        db.session.commit()
        
        return jsonify({
            'message': 'Consulta agendada com sucesso!',
            'id': nova_consulta.id,
            'data': nova_consulta.data.isoformat(),
            'hora': nova_consulta.hora.strftime('%H:%M')
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao criar consulta: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Buscar consulta por ID (GET)
@consulta_bp.route('/<int:consulta_id>', methods=['GET', 'OPTIONS'])
@jwt_required()
def obter_consulta(consulta_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        consulta = Consulta.query.get(consulta_id)
        if not consulta:
            return jsonify({'error': 'Consulta não encontrada'}), 404
        
        paciente = Paciente.query.get(consulta.paciente_id)
        medico = Medico.query.get(consulta.medico_id)
        
        return jsonify({
            'id': consulta.id,
            'paciente_id': consulta.paciente_id,
            'paciente_nome': paciente.nome if paciente else 'Desconhecido',
            'medico_id': consulta.medico_id,
            'medico_nome': medico.nome if medico else 'Desconhecido',
            'especialidade': medico.especialidade if medico else '',
            'data': consulta.data.isoformat(),
            'hora': consulta.hora.strftime('%H:%M'),
            'duracao': consulta.duracao,
            'tipo': consulta.tipo,
            'status': consulta.status,
            'motivo': consulta.motivo or '',
            'observacoes': consulta.observacoes or '',
            'link_teleconsulta': consulta.link_teleconsulta or ''
        }), 200
        
    except Exception as e:
        print(f"❌ Erro ao buscar consulta: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Buscar consultas por paciente (GET)
@consulta_bp.route('/paciente/<int:paciente_id>', methods=['GET', 'OPTIONS'])
@jwt_required()
def consultas_por_paciente(paciente_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(int(current_user_id))
        
        paciente = Paciente.query.get(paciente_id)
        if not paciente:
            return jsonify({'error': 'Paciente não encontrado'}), 404
        
        # Verificar permissão
        if current_user.user_type != 'admin' and current_user.id != paciente.user_id:
            return jsonify({'error': 'Acesso não autorizado'}), 403
        
        consultas = Consulta.query.filter_by(paciente_id=paciente_id).order_by(Consulta.data.desc()).all()
        result = []
        
        for c in consultas:
            medico = Medico.query.get(c.medico_id)
            result.append({
                'id': c.id,
                'medico_id': c.medico_id,
                'medico_nome': medico.nome if medico else 'Desconhecido',
                'especialidade': medico.especialidade if medico else '',
                'data': c.data.isoformat(),
                'hora': c.hora.strftime('%H:%M'),
                'tipo': c.tipo,
                'status': c.status,
                'observacoes': c.observacoes or '',
                'motivo': c.motivo or ''
            })
        
        return jsonify(result), 200
    except Exception as e:
        print(f"❌ Erro ao listar consultas do paciente: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Buscar consultas por médico (GET)
@consulta_bp.route('/medico/<int:medico_id>', methods=['GET', 'OPTIONS'])
@jwt_required()
def consultas_por_medico(medico_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(int(current_user_id))
        
        medico = Medico.query.get(medico_id)
        if not medico:
            return jsonify({'error': 'Médico não encontrado'}), 404
        
        # Verificar permissão
        if current_user.user_type != 'admin' and current_user.id != medico.user_id:
            return jsonify({'error': 'Acesso não autorizado'}), 403
        
        consultas = Consulta.query.filter_by(medico_id=medico_id).order_by(Consulta.data.desc()).all()
        result = []
        
        for c in consultas:
            paciente = Paciente.query.get(c.paciente_id)
            result.append({
                'id': c.id,
                'paciente_id': c.paciente_id,
                'paciente_nome': paciente.nome if paciente else 'Desconhecido',
                'data': c.data.isoformat(),
                'hora': c.hora.strftime('%H:%M'),
                'tipo': c.tipo,
                'status': c.status,
                'observacoes': c.observacoes or '',
                'motivo': c.motivo or ''
            })
        
        return jsonify(result), 200
    except Exception as e:
        print(f"❌ Erro ao listar consultas do médico: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Buscar consultas de hoje (GET)
@consulta_bp.route('/hoje', methods=['GET', 'OPTIONS'])
@jwt_required()
def consultas_hoje():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(int(current_user_id))
        
        hoje = datetime.now().date()
        
        query = Consulta.query.filter_by(data=hoje)
        
        # Se for médico, mostrar apenas suas consultas
        if current_user.user_type == 'medico':
            medico = Medico.query.filter_by(user_id=current_user.id).first()
            if medico:
                query = query.filter_by(medico_id=medico.id)
        
        consultas = query.order_by(Consulta.hora).all()
        result = []
        
        for c in consultas:
            paciente = Paciente.query.get(c.paciente_id)
            medico = Medico.query.get(c.medico_id)
            result.append({
                'id': c.id,
                'paciente_id': c.paciente_id,
                'paciente_nome': paciente.nome if paciente else 'Desconhecido',
                'medico_id': c.medico_id,
                'medico_nome': medico.nome if medico else 'Desconhecido',
                'hora': c.hora.strftime('%H:%M'),
                'tipo': c.tipo,
                'status': c.status
            })
        
        return jsonify(result), 200
    except Exception as e:
        print(f"❌ Erro ao listar consultas de hoje: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Atualizar consulta (PUT)
@consulta_bp.route('/<int:consulta_id>', methods=['PUT', 'OPTIONS'])
@jwt_required()
def atualizar_consulta(consulta_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        consulta = Consulta.query.get(consulta_id)
        if not consulta:
            return jsonify({'error': 'Consulta não encontrada'}), 404
        
        data = request.get_json()
        
        if 'data' in data:
            consulta.data = datetime.strptime(data['data'], '%Y-%m-%d').date()
        if 'hora' in data:
            consulta.hora = datetime.strptime(data['hora'], '%H:%M').time()
        if 'status' in data:
            consulta.status = data['status']
        if 'tipo' in data:
            consulta.tipo = data['tipo']
        if 'motivo' in data:
            consulta.motivo = data['motivo']
        if 'observacoes' in data:
            consulta.observacoes = data['observacoes']
        
        db.session.commit()
        return jsonify({'message': 'Consulta atualizada com sucesso!'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao atualizar consulta: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Cancelar consulta (DELETE)
@consulta_bp.route('/<int:consulta_id>', methods=['DELETE', 'OPTIONS'])
@jwt_required()
def deletar_consulta(consulta_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        consulta = Consulta.query.get(consulta_id)
        if not consulta:
            return jsonify({'error': 'Consulta não encontrada'}), 404
        
        consulta.status = 'cancelada'
        db.session.commit()
        
        return jsonify({'message': 'Consulta cancelada com sucesso!'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao cancelar consulta: {str(e)}")
        return jsonify({'error': str(e)}), 500