# app/models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# NÃO inicialize db aqui! Apenas importe depois
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.Enum('admin', 'medico', 'paciente'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Paciente(db.Model):
    __tablename__ = "pacientes"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True)
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
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    telefone = db.Column(db.String(20))
    registro_oma = db.Column(db.String(20), unique=True)
    especialidade = db.Column(db.String(50))
    formacao = db.Column(db.Text)
    experiencia = db.Column(db.Integer)
    avatar = db.Column(db.String(10))
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Consulta(db.Model):
    __tablename__ = "consultas"
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey("pacientes.id"), nullable=False)
    medico_id = db.Column(db.Integer, db.ForeignKey("medicos.id"), nullable=False)
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
    paciente_id = db.Column(db.Integer, db.ForeignKey("pacientes.id"), nullable=False)
    medico_id = db.Column(db.Integer, db.ForeignKey("medicos.id"), nullable=False)
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
    paciente_id = db.Column(db.Integer, db.ForeignKey("pacientes.id"), nullable=False)
    medico_id = db.Column(db.Integer, db.ForeignKey("medicos.id"), nullable=False)
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