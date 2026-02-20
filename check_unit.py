from app import app, db
from models import Unidade

with app.app_context():
    # Listar todas as unidades disponíveis
    unidades = Unidade.query.all()
    print("Unidades disponíveis:")
    for unidade in unidades:
        print(f"ID: {unidade.id}, Nome: {unidade.nome}")
        
    # Verificar se há uma unidade ativa na sessão (se estiver rodando no contexto da aplicação web)
    try:
        from flask import session
        if 'unit_id' in session:
            print(f"\nUnidade ativa na sessão: {session['unit_id']}")
        else:
            print("\nNenhuma unidade ativa na sessão")
    except:
        print("\nNão foi possível verificar a sessão (fora do contexto da aplicação web)")
