# criar_medicos.py
import sys
import os

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Medico, bcrypt
from datetime import datetime

# Dados dos médicos para cadastrar
medicos_data = [
    {
        "nome": "Dr. Carlos Alberto Silva",
        "email": "carlos.silva@medhistory.ao",
        "telefone": "+244 923 456 001",
        "registro_oma": "12345/OMA",
        "especialidade": "Cardiologia",
        "password": "medico123"
    },
    {
        "nome": "Dra. Ana Paula Santos",
        "email": "ana.santos@medhistory.ao",
        "telefone": "+244 923 456 002",
        "registro_oma": "12346/OMA",
        "especialidade": "Endocrinologia",
        "password": "medico123"
    },
    {
        "nome": "Dr. Roberto Mendes",
        "email": "roberto.mendes@medhistory.ao",
        "telefone": "+244 923 456 003",
        "registro_oma": "12347/OMA",
        "especialidade": "Neurologia",
        "password": "medico123"
    },
    {
        "nome": "Dra. Fernanda Lima",
        "email": "fernanda.lima@medhistory.ao",
        "telefone": "+244 923 456 004",
        "registro_oma": "12348/OMA",
        "especialidade": "Pediatria",
        "password": "medico123"
    },
    {
        "nome": "Dr. Paulo Ricardo",
        "email": "paulo.ricardo@medhistory.ao",
        "telefone": "+244 923 456 005",
        "registro_oma": "12349/OMA",
        "especialidade": "Dermatologia",
        "password": "medico123"
    },
    {
        "nome": "Dra. Mariana Costa",
        "email": "mariana.costa@medhistory.ao",
        "telefone": "+244 923 456 006",
        "registro_oma": "12350/OMA",
        "especialidade": "Ortopedia",
        "password": "medico123"
    }
]

def criar_medicos():
    with app.app_context():
        print("=" * 60)
        print("🚀 Iniciando cadastro de médicos...")
        print("=" * 60)
        
        for medico_data in medicos_data:
            # Verificar se o email já existe
            existing_user = User.query.filter_by(email=medico_data["email"]).first()
            if existing_user:
                print(f"⚠️ Médico {medico_data['email']} já existe! Pulando...")
                continue
            
            # Verificar se o registro OMA já existe
            existing_medico = Medico.query.filter_by(registro_oma=medico_data["registro_oma"]).first()
            if existing_medico:
                print(f"⚠️ Registro OMA {medico_data['registro_oma']} já existe! Pulando...")
                continue
            
            # Criar usuário na tabela users
            password_hash = bcrypt.generate_password_hash(medico_data["password"]).decode('utf-8')
            
            user = User(
                email=medico_data["email"],
                password_hash=password_hash,
                user_type='medico',
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.flush()  # Para obter o user.id
            
            # Criar avatar (iniciais do nome)
            nome_parts = medico_data["nome"].split(' ')
            avatar = nome_parts[0][0].upper()
            if len(nome_parts) > 1:
                avatar += nome_parts[-1][0].upper()
            else:
                avatar += nome_parts[0][1].upper() if len(nome_parts[0]) > 1 else nome_parts[0][0].upper()
            
            # Criar médico na tabela medicos
            medico = Medico(
                user_id=user.id,
                nome=medico_data["nome"],
                email=medico_data["email"],
                telefone=medico_data["telefone"],
                registro_oma=medico_data["registro_oma"],
                especialidade=medico_data["especialidade"],
                avatar=avatar,
                status='active',
                created_at=datetime.utcnow()
            )
            db.session.add(medico)
            
            try:
                db.session.commit()
                print(f"✅ Médico criado com sucesso!")
                print(f"   Nome: {medico_data['nome']}")
                print(f"   Email: {medico_data['email']}")
                print(f"   Senha: {medico_data['password']}")
                print(f"   Especialidade: {medico_data['especialidade']}")
                print(f"   Registro OMA: {medico_data['registro_oma']}")
                print("-" * 50)
            except Exception as e:
                db.session.rollback()
                print(f"❌ Erro ao cadastrar {medico_data['email']}: {str(e)}")
        
        # Listar médicos cadastrados
        print("\n" + "=" * 60)
        print("📋 MÉDICOS CADASTRADOS:")
        print("=" * 60)
        
        medicos = Medico.query.all()
        for m in medicos:
            print(f"ID: {m.id} | Nome: {m.nome} | Email: {m.email} | Especialidade: {m.especialidade} | Status: {m.status}")
        
        print("\n" + "=" * 60)
        print(f"✅ Total de médicos no sistema: {Medico.query.count()}")
        print("=" * 60)

if __name__ == "__main__":
    criar_medicos()