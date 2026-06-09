# app.py - Versão Completa Corrigida com Rota de Receitas e Exames
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy import func
import traceback
import json

app = Flask(__name__)

# Configurações
app.config['SECRET_KEY'] = 'medhistory-super-secret-key-2024'
app.config['JWT_SECRET_KEY'] = 'medhistory-jwt-secret-key-2024-super-seguro-64-caracteres'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/medhistory_ao'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

# Inicializar extensões
CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"], supports_credentials=True)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# ==========================================
# MODELOS
# ==========================================

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Paciente(db.Model):
    __tablename__ = "pacientes"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    telefone = db.Column(db.String(20))
    data_nascimento = db.Column(db.Date)
    genero = db.Column(db.String(20))
    tipo_sanguineo = db.Column(db.String(5))
    endereco = db.Column(db.Text)
    alergias = db.Column(db.Text)
    condicoes_cronicas = db.Column(db.Text)
    avatar = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Medico(db.Model):
    __tablename__ = "medicos"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    telefone = db.Column(db.String(20))
    registro_oma = db.Column(db.String(20), unique=True)
    especialidade = db.Column(db.String(50))
    formacao = db.Column(db.Text)
    experiencia = db.Column(db.Integer)
    avatar = db.Column(db.String(10))
    status = db.Column(db.String(20), default='active')
    horarios_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Consulta(db.Model):
    __tablename__ = "consultas"
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey("pacientes.id"))
    medico_id = db.Column(db.Integer, db.ForeignKey("medicos.id"))
    data = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, nullable=False)
    duracao = db.Column(db.Integer, default=30)
    tipo = db.Column(db.String(20), default='presencial')
    status = db.Column(db.String(20), default='agendada')
    motivo = db.Column(db.Text)
    observacoes = db.Column(db.Text)
    link_teleconsulta = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Exame(db.Model):
    __tablename__ = "exames"
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey("pacientes.id"))
    medico_id = db.Column(db.Integer, db.ForeignKey("medicos.id"))
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(30))
    data_solicitacao = db.Column(db.Date, nullable=False)
    data_realizacao = db.Column(db.Date)
    status = db.Column(db.String(20), default='pendente')
    resultados = db.Column(db.Text)
    arquivo_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Receita(db.Model):
    __tablename__ = "receitas"
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey("pacientes.id"))
    medico_id = db.Column(db.Integer, db.ForeignKey("medicos.id"))
    data_emissao = db.Column(db.Date, nullable=False)
    data_validade = db.Column(db.Date, nullable=False)
    observacoes = db.Column(db.Text)
    status = db.Column(db.String(20), default='ativa')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Medicamento(db.Model):
    __tablename__ = "medicamentos"
    id = db.Column(db.Integer, primary_key=True)
    receita_id = db.Column(db.Integer, db.ForeignKey("receitas.id"), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    dosagem = db.Column(db.String(50))
    frequencia = db.Column(db.String(100))
    duracao = db.Column(db.String(50))
    horario = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ==========================================
# ROTAS DE AUTENTICAÇÃO
# ==========================================

@app.route('/api/auth/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        print(f"📝 Registro de paciente: {data}")
        
        if not data.get('nome') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Nome, email e senha são obrigatórios'}), 400
        
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
        
        avatar = data['nome'][0].upper()
        if len(data['nome'].split(' ')) > 1:
            avatar += data['nome'].split(' ')[1][0].upper()
        
        paciente = Paciente(
            user_id=user.id,
            nome=data['nome'],
            email=data['email'],
            telefone=data.get('telefone', ''),
            data_nascimento=datetime.strptime(data['data_nascimento'], '%Y-%m-%d').date() if data.get('data_nascimento') else None,
            tipo_sanguineo=data.get('tipo_sanguineo'),
            avatar=avatar
        )
        db.session.add(paciente)
        db.session.commit()
        
        return jsonify({'message': 'Paciente cadastrado com sucesso!'}), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/register-medico', methods=['POST', 'OPTIONS'])
def register_medico():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        print(f"📝 Registro de médico: {data}")
        
        if not data.get('nome') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Nome, email e senha são obrigatórios'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email já cadastrado'}), 400
        
        if data.get('registro_oma') and Medico.query.filter_by(registro_oma=data['registro_oma']).first():
            return jsonify({'error': 'Registro OMA já cadastrado'}), 400
        
        password_hash = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        user = User(
            email=data['email'],
            password_hash=password_hash,
            user_type='medico',
            is_active=True
        )
        db.session.add(user)
        db.session.flush()
        
        avatar = data['nome'][0].upper()
        if len(data['nome'].split(' ')) > 1:
            avatar += data['nome'].split(' ')[1][0].upper()
        
        medico = Medico(
            user_id=user.id,
            nome=data['nome'],
            email=data['email'],
            telefone=data.get('telefone', ''),
            registro_oma=data.get('registro_oma', ''),
            especialidade=data.get('especialidade', ''),
            avatar=avatar,
            status='active'
        )
        db.session.add(medico)
        db.session.commit()
        
        print(f"✅ Médico cadastrado: {medico.nome}")
        
        return jsonify({
            'message': 'Médico cadastrado com sucesso!',
            'medico_id': medico.id,
            'email': medico.email
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        print(f"🔐 Tentativa de login: {data.get('email')}")
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not bcrypt.check_password_hash(user.password_hash, data['password']):
            return jsonify({'error': 'Email ou senha inválidos'}), 401
        
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
        
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'access_token': access_token,
            'token_type': 'bearer',
            'user_type': user.user_type,
            'user_id': user.id,
            'nome': nome,
            'avatar': avatar,
            'email': user.email
        }), 200
        
    except Exception as e:
        print(f"❌ Erro no login: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/me', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_current_user():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
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
        
        return jsonify({
            'id': user.id,
            'email': user.email,
            'user_type': user.user_type,
            'nome': nome,
            'avatar': avatar,
            'is_active': user.is_active
        }), 200
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==========================================
# ROTAS DE PACIENTES
# ==========================================

@app.route('/api/pacientes', methods=['GET', 'OPTIONS'])
@jwt_required()
def listar_pacientes():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        pacientes = Paciente.query.all()
        result = []
        for p in pacientes:
            result.append({
                'id': p.id,
                'nome': p.nome,
                'email': p.email,
                'telefone': p.telefone or '',
                'data_nascimento': p.data_nascimento.isoformat() if p.data_nascimento else None,
                'genero': p.genero or '',
                'tipo_sanguineo': p.tipo_sanguineo or '',
                'endereco': p.endereco or '',
                'alergias': p.alergias or '',
                'condicoes_cronicas': p.condicoes_cronicas or '',
                'avatar': p.avatar or p.nome[0].upper(),
                'status': 'active'
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pacientes/usuario/<int:user_id>', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_paciente_by_user(user_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(int(current_user_id))
        
        if not current_user:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        paciente = Paciente.query.filter_by(user_id=user_id).first()
        
        if not paciente:
            return jsonify({'error': 'Paciente não encontrado'}), 404
        
        if current_user.user_type != 'admin' and current_user.id != user_id:
            return jsonify({'error': 'Acesso não autorizado'}), 403
        
        return jsonify({
            'id': paciente.id,
            'nome': paciente.nome,
            'email': paciente.email,
            'telefone': paciente.telefone or '',
            'data_nascimento': paciente.data_nascimento.isoformat() if paciente.data_nascimento else None,
            'genero': paciente.genero or '',
            'tipo_sanguineo': paciente.tipo_sanguineo or '',
            'endereco': paciente.endereco or '',
            'alergias': paciente.alergias or '',
            'condicoes_cronicas': paciente.condicoes_cronicas or '',
            'avatar': paciente.avatar or paciente.nome[0].upper()
        }), 200
        
    except Exception as e:
        print(f"❌ Erro ao buscar paciente: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==========================================
# ROTAS DE MÉDICOS
# ==========================================

@app.route('/api/medicos', methods=['GET', 'OPTIONS'])
@jwt_required()
def listar_medicos():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        medicos = Medico.query.all()
        result = []
        for m in medicos:
            result.append({
                'id': m.id,
                'nome': m.nome,
                'email': m.email,
                'telefone': m.telefone or '',
                'registro_oma': m.registro_oma or '',
                'especialidade': m.especialidade or '',
                'avatar': m.avatar or m.nome[0].upper(),
                'status': m.status
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/medicos/usuario/<int:user_id>', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_medico_by_user(user_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(int(current_user_id))
        
        if not current_user:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        medico = Medico.query.filter_by(user_id=user_id).first()
        
        if not medico:
            return jsonify({'error': 'Médico não encontrado'}), 404
        
        if current_user.user_type != 'admin' and current_user.id != user_id:
            return jsonify({'error': 'Acesso não autorizado'}), 403
        
        # Buscar estatísticas
        total_pacientes = db.session.query(func.count(Consulta.paciente_id.distinct())).filter_by(medico_id=medico.id).scalar() or 0
        total_consultas = Consulta.query.filter_by(medico_id=medico.id).count()
        
        return jsonify({
            'id': medico.id,
            'user_id': medico.user_id,
            'nome': medico.nome,
            'email': medico.email,
            'telefone': medico.telefone or '',
            'registro_oma': medico.registro_oma or '',
            'especialidade': medico.especialidade or '',
            'avatar': medico.avatar or medico.nome[0].upper(),
            'status': medico.status,
            'total_pacientes': total_pacientes,
            'total_consultas': total_consultas,
            'experiencia': getattr(medico, 'experiencia', 0),
            'formacao': getattr(medico, 'formacao', ''),
            'rating': 4.8
        }), 200
        
    except Exception as e:
        print(f"❌ Erro ao buscar médico: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==========================================
# ROTAS DE CONSULTAS
# ==========================================

@app.route('/api/consultas', methods=['GET', 'OPTIONS'])
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

@app.route('/api/consultas', methods=['POST', 'OPTIONS'])
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
            'id': nova_consulta.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao criar consulta: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/consultas/paciente/<int:paciente_id>', methods=['GET', 'OPTIONS'])
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

@app.route('/api/consultas/medico/<int:medico_id>', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_consultas_by_medico(medico_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(int(current_user_id))
        
        # Verificar permissão
        if current_user.user_type == 'medico':
            medico_logado = Medico.query.filter_by(user_id=current_user.id).first()
            if not medico_logado or medico_logado.id != medico_id:
                return jsonify({'error': 'Acesso não autorizado'}), 403
        
        # Parâmetros de filtro
        data_filtro = request.args.get('data')
        proximas = request.args.get('proximas') == 'true'
        passadas = request.args.get('passadas') == 'true'
        
        query = Consulta.query.filter_by(medico_id=medico_id)
        hoje = datetime.now().date()
        
        if data_filtro:
            query = query.filter_by(data=datetime.strptime(data_filtro, '%Y-%m-%d').date())
        elif proximas:
            query = query.filter(Consulta.data >= hoje, Consulta.status != 'cancelada')
        elif passadas:
            query = query.filter(Consulta.data < hoje)
        
        consultas = query.order_by(Consulta.data.asc(), Consulta.hora.asc()).all()
        result = []
        
        for c in consultas:
            paciente = Paciente.query.get(c.paciente_id)
            result.append({
                'id': c.id,
                'paciente_id': c.paciente_id,
                'paciente_nome': paciente.nome if paciente else 'Desconhecido',
                'paciente_avatar': paciente.avatar if paciente else (paciente.nome[0].upper() if paciente else 'P'),
                'data': c.data.isoformat(),
                'hora': c.hora.strftime('%H:%M'),
                'duracao': c.duracao,
                'tipo': c.tipo,
                'status': c.status,
                'motivo': c.motivo or '',
                'observacoes': c.observacoes or '',
                'link_teleconsulta': getattr(c, 'link_teleconsulta', '')
            })
        
        print(f"✅ {len(result)} consultas encontradas para o médico {medico_id}")
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ Erro ao buscar consultas do médico: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/consultas/<int:consulta_id>', methods=['PUT', 'OPTIONS'])
@jwt_required()
def atualizar_consulta(consulta_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        consulta = Consulta.query.get(consulta_id)
        if not consulta:
            return jsonify({'error': 'Consulta não encontrada'}), 404
        
        data = request.get_json()
        
        if 'status' in data:
            consulta.status = data['status']
        if 'observacoes' in data:
            consulta.observacoes = data['observacoes']
        if 'motivo' in data:
            consulta.motivo = data['motivo']
        
        db.session.commit()
        return jsonify({'message': 'Consulta atualizada com sucesso!'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/consultas/<int:consulta_id>', methods=['DELETE', 'OPTIONS'])
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
        return jsonify({'error': str(e)}), 500

# ==========================================
# ROTAS DE PACIENTES POR MÉDICO
# ==========================================

@app.route('/api/pacientes/medico/<int:medico_id>', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_pacientes_by_medico(medico_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(int(current_user_id))
        
        # Verificar permissão
        if current_user.user_type == 'medico':
            medico_logado = Medico.query.filter_by(user_id=current_user.id).first()
            if not medico_logado or medico_logado.id != medico_id:
                return jsonify({'error': 'Acesso não autorizado'}), 403
        
        # Buscar todos os pacientes que tiveram consulta com este médico
        consultas = Consulta.query.filter_by(medico_id=medico_id).all()
        pacientes_ids = set()
        for c in consultas:
            pacientes_ids.add(c.paciente_id)
        
        result = []
        hoje = datetime.now().date()
        
        for pid in pacientes_ids:
            paciente = Paciente.query.get(pid)
            if paciente:
                # Buscar última e próxima consulta
                ultima_consulta = Consulta.query.filter_by(
                    medico_id=medico_id, 
                    paciente_id=pid
                ).filter(Consulta.data < hoje).order_by(Consulta.data.desc()).first()
                
                proxima_consulta = Consulta.query.filter_by(
                    medico_id=medico_id, 
                    paciente_id=pid
                ).filter(Consulta.data >= hoje, Consulta.status != 'cancelada').order_by(Consulta.data.asc()).first()
                
                result.append({
                    'id': paciente.id,
                    'nome': paciente.nome,
                    'email': paciente.email,
                    'telefone': paciente.telefone or '',
                    'avatar': paciente.avatar or paciente.nome[0].upper(),
                    'ultima_consulta': ultima_consulta.data.isoformat() if ultima_consulta else None,
                    'proxima_consulta': proxima_consulta.data.isoformat() if proxima_consulta else None,
                    'data_nascimento': paciente.data_nascimento.isoformat() if paciente.data_nascimento else None,
                    'tipo_sanguineo': paciente.tipo_sanguineo or '',
                    'status': 'novo' if not ultima_consulta else 'regular'
                })
        
        print(f"✅ {len(result)} pacientes encontrados para o médico {medico_id}")
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ Erro ao buscar pacientes do médico: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==========================================
# ROTAS DE EXAMES
# ==========================================

@app.route('/api/exames', methods=['GET', 'OPTIONS'])
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
        return jsonify({'error': str(e)}), 500

@app.route('/api/exames/paciente/<int:paciente_id>', methods=['GET', 'OPTIONS'])
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
        
        if current_user.user_type != 'admin' and current_user.id != paciente.user_id:
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

@app.route('/api/exames', methods=['POST', 'OPTIONS'])
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

@app.route('/api/exames/<int:exame_id>', methods=['PUT', 'OPTIONS'])
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

@app.route('/api/exames/<int:exame_id>', methods=['DELETE', 'OPTIONS'])
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

# ==========================================
# ROTAS DE RECEITAS - CORRIGIDAS
# ==========================================

# LISTAR RECEITAS (GET)
@app.route('/api/receitas', methods=['GET', 'OPTIONS'])
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
            medicamentos_text = []
            for m in medicamentos:
                medicamentos_list.append({
                    'id': m.id,
                    'nome': m.nome,
                    'dosagem': m.dosagem or '',
                    'frequencia': m.frequencia or '',
                    'duracao': m.duracao or '',
                    'horario': m.horario or ''
                })
                medicamentos_text.append(f"{m.nome}{' ' + m.dosagem if m.dosagem else ''}")
            
            # Calcular status baseado na validade
            status = r.status
            if r.data_validade and hoje > r.data_validade:
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
                'data_validade': r.data_validade.isoformat(),
                'medicamentos': ', '.join(medicamentos_text),
                'medicamentos_lista': medicamentos_list,
                'observacoes': r.observacoes or '',
                'status': status
            })
        
        print(f"✅ {len(result)} receitas encontradas")
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ Erro ao listar receitas: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# CRIAR RECEITA (POST)
@app.route('/api/receitas', methods=['POST', 'OPTIONS'])
@jwt_required()
def criar_receita():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(int(current_user_id))
        
        data = request.get_json()
        
        if not data.get('paciente_id'):
            return jsonify({'error': 'Paciente é obrigatório'}), 400
        
        # Verificar se o médico existe
        if current_user.user_type == 'medico':
            medico = Medico.query.filter_by(user_id=current_user.id).first()
            if not medico:
                return jsonify({'error': 'Médico não encontrado'}), 404
            medico_id = medico.id
        else:
            medico_id = data.get('medico_id')
        
        # Verificar se o paciente existe
        paciente = Paciente.query.get(data['paciente_id'])
        if not paciente:
            return jsonify({'error': 'Paciente não encontrado'}), 404
        
        # Calcular data de validade (30 dias a partir da emissão)
        data_emissao = datetime.now().date()
        data_validade = data_emissao + timedelta(days=30)
        if data.get('data_validade'):
            data_validade = datetime.strptime(data['data_validade'], '%Y-%m-%d').date()
        
        # Criar receita
        receita = Receita(
            paciente_id=data['paciente_id'],
            medico_id=medico_id,
            data_emissao=data_emissao,
            data_validade=data_validade,
            observacoes=data.get('observacoes', ''),
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
            'data_validade': receita.data_validade.isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao criar receita: {str(e)}")
        return jsonify({'error': str(e)}), 500

# BUSCAR RECEITAS POR PACIENTE
@app.route('/api/receitas/paciente/<int:paciente_id>', methods=['GET', 'OPTIONS'])
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
            if r.data_validade and hoje > r.data_validade:
                status = 'expirada'
            
            result.append({
                'id': r.id,
                'medicamentos': ', '.join([m.nome for m in medicamentos]),
                'medicamentos_lista': medicamentos_list,
                'observacoes': r.observacoes or '',
                'data_emissao': r.data_emissao.isoformat(),
                'data_validade': r.data_validade.isoformat(),
                'medico_nome': medico.nome if medico else 'Desconhecido',
                'status': status
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ Erro ao listar receitas do paciente: {str(e)}")
        return jsonify({'error': str(e)}), 500

# BUSCAR RECEITA POR ID
@app.route('/api/receitas/<int:receita_id>', methods=['GET', 'OPTIONS'])
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
        if receita.data_validade and hoje > receita.data_validade:
            status = 'expirada'
        
        return jsonify({
            'id': receita.id,
            'paciente_id': receita.paciente_id,
            'paciente_nome': paciente.nome if paciente else 'Desconhecido',
            'medico_id': receita.medico_id,
            'medico_nome': medico.nome if medico else 'Desconhecido',
            'medico_crm': medico.registro_oma if medico else '',
            'data_emissao': receita.data_emissao.isoformat(),
            'data_validade': receita.data_validade.isoformat(),
            'medicamentos_lista': medicamentos_list,
            'observacoes': receita.observacoes or '',
            'status': status
        }), 200
        
    except Exception as e:
        print(f"❌ Erro ao buscar receita: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ATUALIZAR RECEITA
@app.route('/api/receitas/<int:receita_id>', methods=['PUT', 'OPTIONS'])
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
        
        if 'observacoes' in data:
            receita.observacoes = data['observacoes']
        if 'data_validade' in data:
            receita.data_validade = datetime.strptime(data['data_validade'], '%Y-%m-%d').date()
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
        print(f"❌ Erro ao atualizar receita: {str(e)}")
        return jsonify({'error': str(e)}), 500

# DELETAR RECEITA
@app.route('/api/receitas/<int:receita_id>', methods=['DELETE', 'OPTIONS'])
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
        return jsonify({'error': str(e)}), 500

# ==========================================
# ROTAS DE AGENDA/HORÁRIOS DO MÉDICO
# ==========================================

@app.route('/api/medicos/<int:medico_id>/horarios', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_medico_horarios(medico_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(int(current_user_id))
        
        medico = Medico.query.get(medico_id)
        if not medico:
            return jsonify({'error': 'Médico não encontrado'}), 404
        
        if current_user.user_type != 'admin' and current_user.id != medico.user_id:
            return jsonify({'error': 'Acesso não autorizado'}), 403
        
        # Buscar horários salvos
        if medico.horarios_json:
            horarios = json.loads(medico.horarios_json)
        else:
            # Horários padrão para exemplo
            horarios = {
                'monday': ['08:00', '09:00', '10:00', '11:00', '14:00', '15:00', '16:00'],
                'tuesday': ['08:00', '09:00', '10:00', '11:00', '14:00', '15:00', '16:00'],
                'wednesday': ['08:00', '09:00', '10:00', '11:00'],
                'thursday': ['08:00', '09:00', '10:00', '11:00', '14:00', '15:00', '16:00'],
                'friday': ['08:00', '09:00', '10:00', '11:00']
            }
        
        return jsonify(horarios), 200
        
    except Exception as e:
        print(f"❌ Erro ao buscar horários: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/medicos/<int:medico_id>/horarios', methods=['POST', 'OPTIONS'])
@jwt_required()
def adicionar_horario_medico(medico_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(int(current_user_id))
        
        medico = Medico.query.get(medico_id)
        if not medico:
            return jsonify({'error': 'Médico não encontrado'}), 404
        
        if current_user.user_type != 'admin' and current_user.id != medico.user_id:
            return jsonify({'error': 'Acesso não autorizado'}), 403
        
        data = request.get_json()
        dia = data.get('dia')
        horario = data.get('horario')
        
        # Buscar horários atuais
        horarios = {}
        if medico.horarios_json:
            horarios = json.loads(medico.horarios_json)
        else:
            horarios = {
                'monday': [],
                'tuesday': [],
                'wednesday': [],
                'thursday': [],
                'friday': []
            }
        
        if dia in horarios and horario not in horarios[dia]:
            horarios[dia].append(horario)
            horarios[dia].sort()
            medico.horarios_json = json.dumps(horarios)
            db.session.commit()
        
        return jsonify({'message': 'Horário adicionado com sucesso!', 'horarios': horarios}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao adicionar horário: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/medicos/<int:medico_id>/horarios', methods=['DELETE', 'OPTIONS'])
@jwt_required()
def remover_horario_medico(medico_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(int(current_user_id))
        
        medico = Medico.query.get(medico_id)
        if not medico:
            return jsonify({'error': 'Médico não encontrado'}), 404
        
        if current_user.user_type != 'admin' and current_user.id != medico.user_id:
            return jsonify({'error': 'Acesso não autorizado'}), 403
        
        data = request.get_json()
        dia = data.get('dia')
        horario = data.get('horario')
        
        if medico.horarios_json:
            horarios = json.loads(medico.horarios_json)
            if dia in horarios and horario in horarios[dia]:
                horarios[dia].remove(horario)
                medico.horarios_json = json.dumps(horarios)
                db.session.commit()
        
        return jsonify({'message': 'Horário removido com sucesso!'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao remover horário: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==========================================
# ROTA PARA CONCLUIR CONSULTA (MARCAR COMO REALIZADA)
# ==========================================

@app.route('/api/consultas/<int:consulta_id>/concluir', methods=['PUT', 'OPTIONS'])
@jwt_required()
def concluir_consulta(consulta_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        consulta = Consulta.query.get(consulta_id)
        if not consulta:
            return jsonify({'error': 'Consulta não encontrada'}), 404
        
        consulta.status = 'realizada'
        db.session.commit()
        
        return jsonify({'message': 'Consulta marcada como realizada com sucesso!'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao concluir consulta: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==========================================
# ROTA PARA ADICIONAR OBSERVAÇÕES À CONSULTA
# ==========================================

@app.route('/api/consultas/<int:consulta_id>/observacoes', methods=['PUT', 'OPTIONS'])
@jwt_required()
def adicionar_observacoes_consulta(consulta_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        consulta = Consulta.query.get(consulta_id)
        if not consulta:
            return jsonify({'error': 'Consulta não encontrada'}), 404
        
        data = request.get_json()
        observacoes = data.get('observacoes', '')
        
        consulta.observacoes = observacoes
        db.session.commit()
        
        return jsonify({'message': 'Observações adicionadas com sucesso!'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao adicionar observações: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==========================================
# ROTA PARA BUSCAR PRONTUÁRIO DO PACIENTE
# ==========================================

@app.route('/api/pacientes/<int:paciente_id>/prontuario', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_prontuario_paciente(paciente_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(int(current_user_id))
        
        paciente = Paciente.query.get(paciente_id)
        if not paciente:
            return jsonify({'error': 'Paciente não encontrado'}), 404
        
        # Verificar permissão (apenas admin ou médico que atendeu o paciente)
        if current_user.user_type == 'medico':
            medico = Medico.query.filter_by(user_id=current_user.id).first()
            if medico:
                consultas = Consulta.query.filter_by(medico_id=medico.id, paciente_id=paciente_id).all()
                if not consultas:
                    return jsonify({'error': 'Acesso não autorizado'}), 403
        elif current_user.user_type != 'admin':
            return jsonify({'error': 'Acesso não autorizado'}), 403
        
        # Buscar todas as consultas do paciente
        consultas = Consulta.query.filter_by(paciente_id=paciente_id).order_by(Consulta.data.desc()).all()
        consultas_list = []
        for c in consultas:
            medico = Medico.query.get(c.medico_id)
            consultas_list.append({
                'id': c.id,
                'data': c.data.isoformat(),
                'hora': c.hora.strftime('%H:%M'),
                'medico_nome': medico.nome if medico else 'Desconhecido',
                'tipo': c.tipo,
                'status': c.status,
                'motivo': c.motivo or '',
                'observacoes': c.observacoes or ''
            })
        
        # Buscar exames do paciente
        exames = Exame.query.filter_by(paciente_id=paciente_id).order_by(Exame.data_solicitacao.desc()).all()
        exames_list = []
        for e in exames:
            medico = Medico.query.get(e.medico_id)
            exames_list.append({
                'id': e.id,
                'nome': e.nome,
                'data_solicitacao': e.data_solicitacao.isoformat(),
                'data_realizacao': e.data_realizacao.isoformat() if e.data_realizacao else None,
                'medico_nome': medico.nome if medico else 'Desconhecido',
                'resultados': e.resultados or '',
                'status': e.status
            })
        
        # Buscar receitas do paciente
        receitas = Receita.query.filter_by(paciente_id=paciente_id).order_by(Receita.data_emissao.desc()).all()
        receitas_list = []
        for r in receitas:
            medico = Medico.query.get(r.medico_id)
            medicamentos = Medicamento.query.filter_by(receita_id=r.id).all()
            medicamentos_text = ', '.join([m.nome for m in medicamentos])
            receitas_list.append({
                'id': r.id,
                'medicamentos': medicamentos_text,
                'data_emissao': r.data_emissao.isoformat(),
                'data_validade': r.data_validade.isoformat(),
                'medico_nome': medico.nome if medico else 'Desconhecido',
                'observacoes': r.observacoes or ''
            })
        
        return jsonify({
            'paciente': {
                'id': paciente.id,
                'nome': paciente.nome,
                'email': paciente.email,
                'telefone': paciente.telefone or '',
                'data_nascimento': paciente.data_nascimento.isoformat() if paciente.data_nascimento else None,
                'tipo_sanguineo': paciente.tipo_sanguineo or '',
                'alergias': paciente.alergias or '',
                'condicoes_cronicas': paciente.condicoes_cronicas or ''
            },
            'consultas': consultas_list,
            'exames': exames_list,
            'receitas': receitas_list
        }), 200
        
    except Exception as e:
        print(f"❌ Erro ao buscar prontuário: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==========================================
# ROTA PARA ESTATÍSTICAS DETALHADAS DO MÉDICO
# ==========================================

@app.route('/api/medicos/<int:medico_id>/estatisticas', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_medico_estatisticas(medico_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(int(current_user_id))
        
        medico = Medico.query.get(medico_id)
        if not medico:
            return jsonify({'error': 'Médico não encontrado'}), 404
        
        if current_user.user_type != 'admin' and current_user.id != medico.user_id:
            return jsonify({'error': 'Acesso não autorizado'}), 403
        
        hoje = datetime.now().date()
        inicio_mes = hoje.replace(day=1)
        
        # Estatísticas
        total_consultas = Consulta.query.filter_by(medico_id=medico_id).count()
        consultas_este_mes = Consulta.query.filter(
            Consulta.medico_id == medico_id,
            Consulta.data >= inicio_mes
        ).count()
        consultas_hoje = Consulta.query.filter_by(medico_id=medico_id, data=hoje).count()
        consultas_realizadas = Consulta.query.filter_by(medico_id=medico_id, status='realizada').count()
        consultas_canceladas = Consulta.query.filter_by(medico_id=medico_id, status='cancelada').count()
        
        # Pacientes únicos
        pacientes_ids = db.session.query(Consulta.paciente_id).filter_by(medico_id=medico_id).distinct().all()
        total_pacientes = len(pacientes_ids)
        
        # Taxa de ocupação (consultas realizadas / total)
        taxa_ocupacao = 0
        if total_consultas > 0:
            taxa_ocupacao = int((consultas_realizadas / total_consultas) * 100)
        
        return jsonify({
            'total_consultas': total_consultas,
            'consultas_este_mes': consultas_este_mes,
            'consultas_hoje': consultas_hoje,
            'consultas_realizadas': consultas_realizadas,
            'consultas_canceladas': consultas_canceladas,
            'total_pacientes': total_pacientes,
            'taxa_ocupacao': taxa_ocupacao
        }), 200
        
    except Exception as e:
        print(f"❌ Erro ao buscar estatísticas: {str(e)}")
        return jsonify({'error': str(e)}), 500
    # ==========================================
# ROTAS DE MÉDICOS - COMPLETAS
# ==========================================

@app.route('/api/medicos', methods=['GET', 'OPTIONS'])
@jwt_required()
def listar_medicos():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        medicos = Medico.query.all()
        result = []
        for m in medicos:
            result.append({
                'id': m.id,
                'nome': m.nome,
                'email': m.email,
                'telefone': m.telefone or '',
                'registro_oma': m.registro_oma or '',
                'especialidade': m.especialidade or '',
                'avatar': m.avatar or m.nome[0].upper(),
                'status': m.status or 'active'
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/medicos', methods=['POST', 'OPTIONS'])
@jwt_required()
def criar_medico():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        if Medico.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email já cadastrado'}), 400
        
        # Criar usuário
        from werkzeug.security import generate_password_hash
        user = User(
            email=data['email'],
            password_hash=generate_password_hash(data.get('password', 'medico123')),
            user_type='medico',
            is_active=True
        )
        db.session.add(user)
        db.session.flush()
        
        # Criar médico
        avatar = data['nome'][0].upper()
        if len(data['nome'].split(' ')) > 1:
            avatar += data['nome'].split(' ')[1][0].upper()
        
        medico = Medico(
            user_id=user.id,
            nome=data['nome'],
            email=data['email'],
            telefone=data.get('telefone', ''),
            registro_oma=data.get('registro_oma', ''),
            especialidade=data.get('especialidade', ''),
            avatar=avatar,
            status='active'
        )
        db.session.add(medico)
        db.session.commit()
        
        return jsonify({
            'message': 'Médico criado com sucesso',
            'id': medico.id,
            'email': medico.email
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/medicos/<int:medico_id>', methods=['PUT', 'OPTIONS'])
@jwt_required()
def atualizar_medico(medico_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        medico = Medico.query.get_or_404(medico_id)
        data = request.get_json()
        
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
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/medicos/<int:medico_id>', methods=['DELETE', 'OPTIONS'])
@jwt_required()
def deletar_medico(medico_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        medico = Medico.query.get_or_404(medico_id)
        medico.status = 'inactive'
        db.session.commit()
        return jsonify({'message': 'Médico desativado com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ==========================================
# ROTAS DE DASHBOARD
# ==========================================

@app.route('/api/dashboard/stats', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_stats():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        total_pacientes = Paciente.query.count()
        total_medicos = Medico.query.count()
        consultas_hoje = Consulta.query.filter_by(data=datetime.now().date()).count()
        
        return jsonify({
            'total_pacientes': total_pacientes,
            'total_medicos': total_medicos,
            'consultas_hoje': consultas_hoje,
            'taxa_ocupacao': 75
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/atividades', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_atividades():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        consultas = Consulta.query.order_by(Consulta.created_at.desc()).limit(10).all()
        atividades = []
        
        for c in consultas:
            paciente = Paciente.query.get(c.paciente_id)
            medico = Medico.query.get(c.medico_id)
            atividades.append({
                'id': c.id,
                'type': 'consulta',
                'patient': paciente.nome if paciente else 'Desconhecido',
                'doctor': medico.nome if medico else 'Desconhecido',
                'time': c.hora.strftime('%H:%M') if c.hora else '',
                'status': c.status,
                'avatar': paciente.avatar if paciente else 'PT'
            })
        
        if not atividades:
            atividades = [
                {'id': 1, 'type': 'consulta', 'patient': 'Maria Silva', 'doctor': 'Dr. Costa', 'time': '10:30', 'status': 'confirmada', 'avatar': 'MS'},
                {'id': 2, 'type': 'consulta', 'patient': 'João Santos', 'doctor': 'Dra. Lima', 'time': '09:15', 'status': 'realizada', 'avatar': 'JS'}
            ]
        
        return jsonify(atividades), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

# ==========================================
# ROTA DE TESTE
# ==========================================

@app.route('/api/teste', methods=['GET'])
def teste():
    return jsonify({'message': 'API funcionando!', 'status': 'online'}), 200

# ==========================================
# ROTAS ADICIONAIS
# ==========================================

# Atualizar paciente (PUT)
@app.route('/api/pacientes/<int:paciente_id>', methods=['PUT', 'OPTIONS'])
@jwt_required()
def atualizar_paciente(paciente_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        paciente = Paciente.query.get(paciente_id)
        if not paciente:
            return jsonify({'error': 'Paciente não encontrado'}), 404
        
        data = request.get_json()
        
        if 'nome' in data:
            paciente.nome = data['nome']
        if 'email' in data:
            paciente.email = data['email']
        if 'telefone' in data:
            paciente.telefone = data['telefone']
        if 'data_nascimento' in data and data['data_nascimento']:
            paciente.data_nascimento = datetime.strptime(data['data_nascimento'], '%Y-%m-%d').date()
        if 'genero' in data:
            paciente.genero = data['genero']
        if 'tipo_sanguineo' in data:
            paciente.tipo_sanguineo = data['tipo_sanguineo']
        if 'endereco' in data:
            paciente.endereco = data['endereco']
        if 'alergias' in data:
            paciente.alergias = data['alergias']
        if 'condicoes_cronicas' in data:
            paciente.condicoes_cronicas = data['condicoes_cronicas']
        
        db.session.commit()
        return jsonify({'message': 'Paciente atualizado com sucesso!'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Deletar paciente (DELETE)
@app.route('/api/pacientes/<int:paciente_id>', methods=['DELETE', 'OPTIONS'])
@jwt_required()
def deletar_paciente(paciente_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        paciente = Paciente.query.get(paciente_id)
        if not paciente:
            return jsonify({'error': 'Paciente não encontrado'}), 404
        
        # Soft delete
        user = User.query.get(paciente.user_id)
        if user:
            user.is_active = False
        
        db.session.delete(paciente)
        db.session.commit()
        
        return jsonify({'message': 'Paciente removido com sucesso!'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ==========================================
# INICIALIZAÇÃO
# ==========================================

def init_db():
    with app.app_context():
        try:
            db.create_all()
            print("✅ Tabelas verificadas/criadas")
            
            admin = User.query.filter_by(email='admin@medhistory.ao').first()
            if not admin:
                admin_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
                admin = User(
                    email='admin@medhistory.ao',
                    password_hash=admin_password,
                    user_type='admin',
                    is_active=True
                )
                db.session.add(admin)
                db.session.commit()
                print("✅ ADMIN CRIADO! Email: admin@medhistory.ao / Senha: admin123")
            else:
                print("✅ Admin já existe!")
            
            # Criar médico de exemplo se não existir
            if Medico.query.count() == 0:
                # Criar usuário médico
                user = User.query.filter_by(email='dr.carlos@medico.com').first()
                if not user:
                    user = User(
                        email='dr.carlos@medico.com',
                        password_hash=bcrypt.generate_password_hash('medico123').decode('utf-8'),
                        user_type='medico',
                        is_active=True
                    )
                    db.session.add(user)
                    db.session.flush()
                
                medico = Medico(
                    user_id=user.id,
                    nome='Dr. Carlos Silva',
                    email='dr.carlos@medico.com',
                    telefone='923456001',
                    registro_oma='12345/OMA',
                    especialidade='Cardiologia',
                    avatar='CS',
                    status='active',
                    experiencia=10,
                    formacao='Universidade Agostinho Neto'
                )
                db.session.add(medico)
                db.session.commit()
                print("✅ Médico de exemplo criado: dr.carlos@medico.com / senha: medico123")
            
            medicos = Medico.query.all()
            print(f"📋 Médicos cadastrados: {len(medicos)}")
            for m in medicos:
                print(f"   - {m.nome} ({m.email})")
            
        except Exception as e:
            print(f"❌ Erro na inicialização: {str(e)}")
            print(traceback.format_exc())
            

init_db()


if __name__ == "__main__":
    print("=" * 50)
    print(" SERVIDOR RODANDO")
    print(f" http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)