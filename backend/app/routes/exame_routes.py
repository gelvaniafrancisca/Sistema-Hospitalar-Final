# app/routes/exame_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Exame, Medico, Paciente, User
from datetime import datetime
import traceback

exame_bp = Blueprint('exames', __name__, url_prefix='/api/exames')

# Listar todos os exames
@exame_bp.route('/', methods=['GET', 'OPTIONS'])
@jwt_required()
def listar_exames():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(int(current_user_id))
        
        # Buscar exames baseado no tipo de usuário
        if current_user.user_type == 'medico':
            medico = Medico.query.filter_by(user_id=current_user.id).first()
            if medico:
                exames = Exame.query.filter_by(medico_id=medico.id).order_by(Exame.data_solicitacao.desc()).all()
            else:
                exames = []
        elif current_user.user_type == 'paciente':
            paciente = Paciente.query.filter_by(user_id=current_user.id).first()
            if paciente:
                exames = Exame.query.filter_by(paciente_id=paciente.id).order_by(Exame.data_solicitacao.desc()).all()
            else:
                exames = []
        else:
            exames = Exame.query.order_by(Exame.data_solicitacao.desc()).all()
        
        result = []
        for e in exames:
            paciente = Paciente.query.get(e.paciente_id)
            medico = Medico.query.get(e.medico_id)
            result.append({
                'id': e.id,
                'nome': e.nome,
                'paciente_id': e.paciente_id,
                'paciente_nome': paciente.nome if paciente else 'Desconhecido',
                'paciente_avatar': paciente.avatar if paciente else (paciente.nome[0].upper() if paciente else 'P'),
                'medico_id': e.medico_id,
                'medico_nome': medico.nome if medico else 'Desconhecido',
                'data_solicitacao': e.data_solicitacao.isoformat(),
                'data_realizacao': e.data_realizacao.isoformat() if e.data_realizacao else None,
                'tipo': e.tipo,
                'status': e.status,
                'resultados': e.resultados or '',
                'arquivo_url': e.arquivo_url or ''
            })
        
        print(f"✅ {len(result)} exames encontrados")
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ Erro ao listar exames: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# Buscar exames por paciente
@exame_bp.route('/paciente/<int:paciente_id>', methods=['GET', 'OPTIONS'])
@jwt_required()
def exames_por_paciente(paciente_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(int(current_user_id))
        
        paciente = Paciente.query.get(paciente_id)
        if not paciente:
            return jsonify({'error': 'Paciente não encontrado'}), 404
        
        # Verificar permissão
        if current_user.user_type == 'paciente' and current_user.id != paciente.user_id:
            return jsonify({'error': 'Acesso não autorizado'}), 403
        
        exames = Exame.query.filter_by(paciente_id=paciente_id).order_by(Exame.data_solicitacao.desc()).all()
        result = []
        
        for e in exames:
            medico = Medico.query.get(e.medico_id)
            result.append({
                'id': e.id,
                'nome': e.nome,
                'tipo': e.tipo,
                'data_solicitacao': e.data_solicitacao.isoformat(),
                'data_realizacao': e.data_realizacao.isoformat() if e.data_realizacao else None,
                'medico_nome': medico.nome if medico else 'Desconhecido',
                'resultados': e.resultados or '',
                'status': e.status,
                'arquivo_url': e.arquivo_url or ''
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ Erro ao listar exames do paciente: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Criar novo exame
@exame_bp.route('/', methods=['POST', 'OPTIONS'])
@jwt_required()
def criar_exame():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(int(current_user_id))
        
        data = request.get_json()
        
        if not data.get('nome') or not data.get('paciente_id'):
            return jsonify({'error': 'Nome do exame e paciente são obrigatórios'}), 400
        
        # Verificar se o paciente existe
        paciente = Paciente.query.get(data['paciente_id'])
        if not paciente:
            return jsonify({'error': 'Paciente não encontrado'}), 404
        
        # Buscar médico logado
        medico = Medico.query.filter_by(user_id=current_user.id).first()
        if not medico:
            return jsonify({'error': 'Médico não encontrado'}), 404
        
        data_solicitacao = datetime.now().date()
        if data.get('data_solicitacao'):
            data_solicitacao = datetime.strptime(data['data_solicitacao'], '%Y-%m-%d').date()
        
        novo_exame = Exame(
            paciente_id=data['paciente_id'],
            medico_id=medico.id,
            nome=data['nome'],
            tipo=data.get('tipo', 'outros'),
            data_solicitacao=data_solicitacao,
            data_realizacao=datetime.strptime(data['data_realizacao'], '%Y-%m-%d').date() if data.get('data_realizacao') else None,
            status='pendente',
            resultados=data.get('resultados', ''),
            arquivo_url=data.get('arquivo_url', '')
        )
        
        db.session.add(novo_exame)
        db.session.commit()
        
        return jsonify({
            'message': 'Exame solicitado com sucesso!',
            'id': novo_exame.id,
            'status': novo_exame.status
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao criar exame: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Atualizar exame
@exame_bp.route('/<int:exame_id>', methods=['PUT', 'OPTIONS'])
@jwt_required()
def atualizar_exame(exame_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        exame = Exame.query.get(exame_id)
        if not exame:
            return jsonify({'error': 'Exame não encontrado'}), 404
        
        data = request.get_json()
        
        if 'resultados' in data:
            exame.resultados = data['resultados']
        if 'status' in data:
            exame.status = data['status']
        if 'data_realizacao' in data and data['data_realizacao']:
            exame.data_realizacao = datetime.strptime(data['data_realizacao'], '%Y-%m-%d').date()
        if 'arquivo_url' in data:
            exame.arquivo_url = data['arquivo_url']
        
        # Se tiver resultados, marcar como concluído
        if exame.resultados and exame.status == 'pendente':
            exame.status = 'concluido'
            if not exame.data_realizacao:
                exame.data_realizacao = datetime.now().date()
        
        db.session.commit()
        
        return jsonify({'message': 'Exame atualizado com sucesso!'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao atualizar exame: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Deletar exame
@exame_bp.route('/<int:exame_id>', methods=['DELETE', 'OPTIONS'])
@jwt_required()
def deletar_exame(exame_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(int(current_user_id))
        
        # Apenas admin pode deletar exames
        if current_user.user_type != 'admin':
            return jsonify({'error': 'Acesso não autorizado'}), 403
        
        exame = Exame.query.get(exame_id)
        if not exame:
            return jsonify({'error': 'Exame não encontrado'}), 404
        
        db.session.delete(exame)
        db.session.commit()
        
        return jsonify({'message': 'Exame removido com sucesso!'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500