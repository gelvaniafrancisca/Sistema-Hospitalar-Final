# migrate_db.py
from app import app, db
from sqlalchemy import text

with app.app_context():
    print("🔧 Migrando banco de dados...")
    
    # Adicionar colunas na tabela consultas
    colunas_consultas = [
        ("tipo", "VARCHAR(20) DEFAULT 'presencial'"),
        ("motivo", "TEXT"),
        ("duracao", "INTEGER DEFAULT 30"),
        ("updated_at", "DATETIME")
    ]
    
    for coluna, tipo in colunas_consultas:
        try:
            db.session.execute(text(f"ALTER TABLE consultas ADD COLUMN {coluna} {tipo}"))
            db.session.commit()
            print(f"✅ Coluna '{coluna}' adicionada")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print(f"✅ Coluna '{coluna}' já existe")
            else:
                print(f"⚠️ Erro ao adicionar {coluna}: {e}")
    
    # Adicionar coluna status na tabela medicos
    try:
        db.session.execute(text("ALTER TABLE medicos ADD COLUMN status VARCHAR(20) DEFAULT 'active'"))
        db.session.commit()
        print("✅ Coluna 'status' adicionada à tabela medicos")
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            print("✅ Coluna 'status' já existe")
        else:
            print(f"⚠️ {e}")
    
    print(" Migração concluída!")