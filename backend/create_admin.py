# create_admin.py
from app import app, db
from app import User
from flask_bcrypt import Bcrypt
import traceback

bcrypt = Bcrypt(app)

with app.app_context():
    try:
        # Verificar se admin já existe
        admin = User.query.filter_by(email='admin@medhistory.ao').first()
        
        if admin:
            print(f"✅ Admin já existe: {admin.email}")
            # Resetar senha
            admin.password_hash = bcrypt.generate_password_hash('admin123').decode('utf-8')
            db.session.commit()
            print("🔑 Senha resetada para: admin123")
        else:
            # Criar novo admin
            password_hash = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin = User(
                email='admin@medhistory.ao',
                password_hash=password_hash,
                user_type='admin',
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            print("=" * 50)
            print("✅ ADMIN CRIADO COM SUCESSO!")
            print(f"📧 Email: admin@medhistory.ao")
            print(f"🔑 Senha: admin123")
            print("=" * 50)
        
        # Listar todos os usuários
        users = User.query.all()
        print(f"\n📋 Total de usuários no banco: {len(users)}")
        for u in users:
            print(f"   - {u.email} ({u.user_type})")
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        print(traceback.format_exc())