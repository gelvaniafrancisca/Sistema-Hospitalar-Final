from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Notificacao, Consulta, Exame, Paciente, Medico
from datetime import datetime, timedelta

notificacao_bp = Blueprint('notificacoes', __name__, url_prefix='/api/notificacoes')

# Listar notificações do usuário
@notificacao_bp.route('/', methods=['GET'])
@jwt_required()
def listar_notificacoes():
    user_id = int(get_jwt_identity())
    
    notificacoes = Notificacao.query.filter_by(
        user_id=user_id
    ).order_by(Notificacao.created_at.desc()).all()
    
    return jsonify([{
        'id': n.id,
        'titulo': n.titulo,
        'mensagem': n.mensagem,
        'tipo': n.tipo,
        'lida': n.lida,
        'created_at': n.created_at.isoformat()
    } for n in notificacoes]), 200

# Marcar como lida
@notificacao_bp.route('/<int:notificacao_id>/ler', methods=['PUT'])
@jwt_required()
def marcar_como_lida(notificacao_id):
    user_id = int(get_jwt_identity())
    
    notificacao = Notificacao.query.get_or_404(notificacao_id)
    
    if notificacao.user_id != user_id:
        return jsonify({'error': 'Acesso negado'}), 403
    
    notificacao.lida = True
    db.session.commit()
    
    return jsonify({'message': 'Notificação marcada como lida'}), 200

# Marcar todas como lidas
@notificacao_bp.route('/marcar-todas', methods=['PUT'])
@jwt_required()
def marcar_todas_como_lidas():
    user_id = int(get_jwt_identity())
    
    Notificacao.query.filter_by(user_id=user_id, lida=False).update({'lida': True})
    db.session.commit()
    
    return jsonify({'message': 'Todas notificações marcadas como lidas'}), 200

# Deletar notificação
@notificacao_bp.route('/<int:notificacao_id>', methods=['DELETE'])
@jwt_required()
def deletar_notificacao(notificacao_id):
    user_id = int(get_jwt_identity())
    
    notificacao = Notificacao.query.get_or_404(notificacao_id)
    
    if notificacao.user_id != user_id:
        return jsonify({'error': 'Acesso negado'}), 403
    
    db.session.delete(notificacao)
    db.session.commit()
    
    return jsonify({'message': 'Notificação removida'}), 200

# Criar notificações automáticas
def criar_notificacao_consulta(consulta_id):
    from app import create_app
    consulta = Consulta.query.get(consulta_id)
    if not consulta:
        return
    
    paciente = Paciente.query.get(consulta.paciente_id)
    medico = Medico.query.get(consulta.medico_id)
    
    if paciente and paciente.user_id:
        # Notificação para o paciente
        notif_paciente = Notificacao(
            user_id=paciente.user_id,
            titulo='Nova Consulta Agendada',
            mensagem=f'Sua consulta com {medico.nome} foi agendada para {consulta.data.strftime("%d/%m/%Y")} às {consulta.hora.strftime("%H:%M")}',
            tipo='consulta'
        )
        db.session.add(notif_paciente)
    
    if medico and medico.user_id:
        # Notificação para o médico
        notif_medico = Notificacao(
            user_id=medico.user_id,
            titulo='Nova Consulta Agendada',
            mensagem=f'Nova consulta com {paciente.nome} agendada para {consulta.data.strftime("%d/%m/%Y")} às {consulta.hora.strftime("%H:%M")}',
            tipo='consulta'
        )
        db.session.add(notif_medico)
    
    db.session.commit()

def criar_notificacao_lembrete():
    """Criar lembretes para consultas do dia seguinte"""
    amanha = datetime.now().date() + timedelta(days=1)
    
    consultas = Consulta.query.filter_by(data=amanha, status='agendada').all()
    
    for consulta in consultas:
        paciente = Paciente.query.get(consulta.paciente_id)
        if paciente and paciente.user_id:
            notificacao = Notificacao(
                user_id=paciente.user_id,
                titulo='Lembrete de Consulta',
                mensagem=f'Você tem uma consulta amanhã às {consulta.hora.strftime("%H:%M")}',
                tipo='consulta'
            )
            db.session.add(notificacao)
    
    db.session.commit()