import os
import sqlite3
from app import db_manager

def listar_unidades():
    """Lista todas as unidades disponíveis"""
    print("\nUnidades disponíveis:")
    print("-" * 50)
    
    # Lista os arquivos de banco de dados na pasta instance
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    if not os.path.exists(instance_dir):
        print("Diretório 'instance' não encontrado.")
        return []
    
    # Lista todos os arquivos .db
    dbs = [f for f in os.listdir(instance_dir) if f.endswith('.db') and f != 'central.db']
    
    if not dbs:
        print("Nenhum banco de dados de unidade encontrado.")
        return []
    
    for i, db_file in enumerate(dbs, 1):
        unit_id = os.path.splitext(db_file)[0]
        print(f"{i}. {unit_id} ({db_file})")
    
    return dbs

def recriar_banco(unit_id):
    """Recria o banco de dados da unidade especificada"""
    # Caminho para o arquivo do banco de dados
    db_path = os.path.join('instance', f"{unit_id}.db")
    backup_path = os.path.join('instance', 'backups', f"{unit_id}_backup.db")
    
    # Criar diretório de backup se não existir
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    
    # Fazer backup do banco existente, se houver
    if os.path.exists(db_path):
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"\nBackup criado em: {backup_path}")
    
    # Remover o banco de dados existente
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Banco de dados antigo removido: {db_path}")
    
    # Recriar o banco de dados
    try:
        # Obter uma conexão para forçar a criação do banco
        conn = db_manager.get_connection(unit_id)
        
        # Inicializar o esquema do banco
        db_manager.init_database(unit_id)
        
        print(f"\n✅ Banco de dados recriado com sucesso: {db_path}")
        print("A tabela 'categorias' foi criada com sucesso!")
        
        # Verificar se a tabela foi criada
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='categorias'")
        if cursor.fetchone():
            print("✅ Tabela 'categorias' verificada com sucesso!")
        else:
            print("❌ Erro: A tabela 'categorias' não foi criada corretamente.")
            
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Erro ao recriar o banco de dados: {str(e)}")
        # Restaurar o backup em caso de erro
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, db_path)
            print(f"Banco de dados restaurado do backup: {db_path}")

if __name__ == '__main__':
    print("🔧 Assistente de Recriação de Banco de Dados da Unidade")
    print("=" * 60)
    
    # Listar unidades disponíveis
    dbs = listar_unidades()
    if not dbs:
        print("\nNenhum banco de dados de unidade encontrado.")
        print("Certifique-se de que o sistema foi instalado corretamente.")
        exit(1)
    
    # Pedir ao usuário para selecionar uma unidade
    while True:
        try:
            opcao = input("\nDigite o número da unidade para recriar o banco (ou 'sair' para cancelar): ")
            if opcao.lower() == 'sair':
                print("Operação cancelada.")
                exit(0)
                
            opcao = int(opcao)
            if 1 <= opcao <= len(dbs):
                break
            else:
                print(f"Por favor, digite um número entre 1 e {len(dbs)}.")
        except ValueError:
            print("Por favor, digite um número válido.")
    
    # Confirmar a operação
    unit_id = os.path.splitext(dbs[opcao-1])[0]
    print(f"\n⚠️  ATENÇÃO: Esta operação irá recriar o banco de dados da unidade: {unit_id}")
    print("TODOS OS DADOS ATUAIS SERÃO PERDIDOS, exceto o backup que será criado.")
    
    confirmacao = input("\nTem certeza que deseja continuar? (s/n): ")
    if confirmacao.lower() != 's':
        print("Operação cancelada pelo usuário.")
        exit(0)
    
    # Executar a recriação do banco
    recriar_banco(unit_id)
    
    print("\n✅ Processo concluído. Você pode acessar o sistema normalmente agora.")
