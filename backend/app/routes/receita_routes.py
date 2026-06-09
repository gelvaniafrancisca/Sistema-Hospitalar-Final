# app/routes/receita_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Receita, Medicamento, Medico, Paciente, User
from datetime import datetime, timedelta
import traceback

receita_bp = Blueprint('receitas', __name__, url_prefix='/api/receitas')

# Listar todas as receitas
@receita_bp.route('/', methods=['GET', 'OPTIONS'])
@jwt_required()
def listar_receitas():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(int(current_user_id))
        
        # Buscar receitas baseado no tipo de usuário
        if current_user.user_type == 'medico':
            medico = Medico.query.filter_by(user_id=current_user.id).first()
            if medico:
                receitas = Receita.query.filter_by(medico_id=medico.id).order_by(Receita.data_emissao.desc()).all()
            else:
                receitas = []
        elif current_user.user_type == 'paciente':
            paciente = Paciente.query.filter_by(user_id=current_user.id).first()
            if paciente:
                receitas = Receita.query.filter_by(paciente_id=paciente.id).order_by(Receita.data_emissao.desc()).all()
            else:
                receitas = []
        else:
            receitas = Receita.query.order_by(Receita.data_emissao.desc()).all()
        
        result = []
        hoje = datetime.now().date()
        
        for r in receitas:
            paciente = Paciente.query.get(r.paciente_id)
            medico = Medico.query.get(r.medico_id)
            
            # Buscar medicamentos da receita
            medicamentos = Medicamento.query.filter_by(receita_id=r.id).all()
            medicamentos_list = []
            for m in medicamentos:
                medicamentos_list.append({
                    'nome': m.nome,
                    'dosagem': m.dosagem,
                    'frequencia': m.frequencia,
                    'duracao': m.duracao,
                    'horario': m.horario
                })
            
            # Verificar se está expirada
            status = r.status
            if r.validade and hoje > r.validade:
                status = 'expirada'
            
            result.append({
                'id': r.id,
                'paciente_id': r.paciente_id,
                'paciente_nome': paciente.nome if paciente else 'Desconhecido',
                'paciente_avatar': paciente.avatar if paciente else (paciente.nome[0].upper() if paciente else 'P'),
                'medico_id': r.medico_id,
                'medico_nome': medico.nome if medico else 'Desconhecido',
                'medico_crm': medico.registro_oma if medico else '',
                'data_emissao': r.data_emissao.isoformat(),
                'validade': r.validade.isoformat(),
                'medicamentos': r.medicamentos,
                'medicamentos_lista': medicamentos_list,
                'instrucoes': r.instrucoes or '',
                'status': status
            })
        
        print(f"✅ {len(result)} receitas encontradas")
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ Erro ao listar receitas: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# Buscar receitas por paciente
@receita_bp.route('/paciente/<int:paciente_id>', methods=['GET', 'OPTIONS'])
@jwt_required()
def receitas_por_paciente(paciente_id):
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
        
        receitas = Receita.query.filter_by(paciente_id=paciente_id).order_by(Receita.data_emissao.desc()).all()
        result = []
        hoje = datetime.now().date()
        
        for r in receitas:
            medico = Medico.query.get(r.medico_id)
            
            medicamentos = Medicamento.query.filter_by(receita_id=r.id).all()
            medicamentos_list = []
            for m in medicamentos:
                medicamentos_list.append({
                    'nome': m.nome,
                    'dosagem': m.dosagem,
                    'frequencia': m.frequencia,
                    'duracao': m.duracao,
                    'horario': m.horario
                })
            
            status = r.status
            if r.validade and hoje > r.validade:
                status = 'expirada'
            
            result.append({
                'id': r.id,
                'medicamentos': r.medicamentos,
                'medicamentos_lista': medicamentos_list,
                'instrucoes': r.instrucoes or '',
                'data_emissao': r.data_emissao.isoformat(),
                'validade': r.validade.isoformat(),
                'medico_nome': medico.nome if medico else 'Desconhecido',
                'status': status
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ Erro ao listar receitas do paciente: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Buscar receita por ID
@receita_bp.route('/<int:receita_id>', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_receita(receita_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        receita = Receita.query.get(receita_id)
        if not receita:
            return jsonify({'error': 'Receita não encontrada'}), 404
        
        paciente = Paciente.query.get(receita.paciente_id)
        medico = Medico.query.get(receita.medico_id)
        
        medicamentos = Medicamento.query.filter_by(receita_id=receita.id).all()
        medicamentos_list = []
        for m in medicamentos:
            medicamentos_list.append({
                'id': m.id,
                'nome': m.nome,
                'dosagem': m.dosagem,
                'frequencia': m.frequencia,
                'duracao': m.duracao,
                'horario': m.horario
            })
        
        hoje = datetime.now().date()
        status = receita.status
        if receita.validade and hoje > receita.validade:
            status = 'expirada'
        
        return jsonify({
            'id': receita.id,
            'paciente_id': receita.paciente_id,
            'paciente_nome': paciente.nome if paciente else 'Desconhecido',
            'paciente_avatar': paciente.avatar if paciente else (paciente.nome[0].upper() if paciente else 'P'),
            'medico_id': receita.medico_id,
            'medico_nome': medico.nome if medico else 'Desconhecido',
            'medico_crm': medico.registro_oma if medico else '',
            'data_emissao': receita.data_emissao.isoformat(),
            'validade': receita.validade.isoformat(),
            'medicamentos': receita.medicamentos,
            'medicamentos_lista': medicamentos_list,
            'instrucoes': receita.instrucoes or '',
            'status': status
        }), 200
        
    except Exception as e:
        print(f"❌ Erro ao buscar receita: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Criar nova receita
@receita_bp.route('/', methods=['POST', 'OPTIONS'])
@jwt_required()
def criar_receita():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(int(current_user_id))
        
        data = request.get_json()
        
        if not data.get('paciente_id') or not data.get('medicamentos'):
            return jsonify({'error': 'Paciente e medicamentos são obrigatórios'}), 400
        
        # Verificar se o paciente existe
        paciente = Paciente.query.get(data['paciente_id'])
        if not paciente:
            return jsonify({'error': 'Paciente não encontrado'}), 404
        
        # Buscar médico logado
        medico = Medico.query.filter_by(user_id=current_user.id).first()
        if not medico:
            return jsonify({'error': 'Médico não encontrado'}), 404
        
        # Calcular data de validade (30 dias a partir da emissão)
        data_emissao = datetime.now().date()
        data_validade = data_emissao + timedelta(days=30)
        if data.get('validade'):
            data_validade = datetime.strptime(data['validade'], '%Y-%m-%d').date()
        
        # Criar receita
        receita = Receita(
            paciente_id=data['paciente_id'],
            medico_id=medico.id,
            medicamentos=data['medicamentos'],
            instrucoes=data.get('instrucoes', ''),
            data_emissao=data_emissao,
            validade=data_validade,
            status='ativa'
        )
        db.session.add(receita)
        db.session.flush()
        
        # Criar medicamentos individuais se fornecidos como lista
        if data.get('medicamentos_lista'):
            for med in data['medicamentos_lista']:
                if med.get('nome'):
                    medicamento = Medicamento(
                        receita_id=receita.id,
                        nome=med['nome'],
                        dosagem=med.get('dosagem', ''),
                        frequencia=med.get('frequencia', ''),
                        duracao=med.get('duracao', ''),
                        horario=med.get('horario', '')
                    )
                    db.session.add(medicamento)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Receita emitida com sucesso!',
            'receita_id': receita.id,
            'data_emissao': receita.data_emissao.isoformat(),
            'data_validade': receita.validade.isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f" Erro ao criar receita: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Atualizar receita
@receita_bp.route('/<int:receita_id>', methods=['PUT', 'OPTIONS'])
@jwt_required()
def atualizar_receita(receita_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(int(current_user_id))
        
        receita = Receita.query.get(receita_id)
        if not receita:
            return jsonify({'error': 'Receita não encontrada'}), 404
        
        # Verificar permissão
        if current_user.user_type != 'admin' and current_user.user_type != 'medico':
            return jsonify({'error': 'Acesso não autorizado'}), 403
        
        data = request.get_json()
        
        if 'medicamentos' in data:
            receita.medicamentos = data['medicamentos']
        if 'instrucoes' in data:
            receita.instrucoes = data['instrucoes']
        if 'validade' in data:
            receita.validade = datetime.strptime(data['validade'], '%Y-%m-%d').date()
        if 'status' in data:
            receita.status = data['status']
        
        # Atualizar medicamentos
        if data.get('medicamentos_lista'):
            # Remover medicamentos antigos
            Medicamento.query.filter_by(receita_id=receita.id).delete()
            
            # Adicionar novos medicamentos
            for med in data['medicamentos_lista']:
                if med.get('nome'):
                    medicamento = Medicamento(
                        receita_id=receita.id,
                        nome=med['nome'],
                        dosagem=med.get('dosagem', ''),
                        frequencia=med.get('frequencia', ''),
                        duracao=med.get('duracao', ''),
                        horario=med.get('horario', '')
                    )
                    db.session.add(medicamento)
        
        db.session.commit()
        
        return jsonify({'message': 'Receita atualizada com sucesso!'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f" Erro ao atualizar receita: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Deletar receita
@receita_bp.route('/<int:receita_id>', methods=['DELETE', 'OPTIONS'])
@jwt_required()
def deletar_receita(receita_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(int(current_user_id))
        
        # Apenas admin pode deletar receitas
        if current_user.user_type != 'admin':
            return jsonify({'error': 'Acesso não autorizado'}), 403
        
        receita = Receita.query.get(receita_id)
        if not receita:
            return jsonify({'error': 'Receita não encontrada'}), 404
        
        # Remover medicamentos associados
        Medicamento.query.filter_by(receita_id=receita.id).delete()
        
        db.session.delete(receita)
        db.session.commit()
        
        return jsonify({'message': 'Receita removida com sucesso!'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao deletar receita: {str(e)}")
        return jsonify({'error': str(e)}), 500