"""Script de inicialização: cria o banco central e os bancos de cada unidade definidos em database_config.DATABASES

Execute:
    python scripts/init_all_dbs.py
"""
from database_manager import db_manager
from database_config import DATABASES

def main():
    print('Inicializando banco central...')
    db_manager.init_database(None)
    print('Banco central inicializado.')

    for unit_id in DATABASES.keys():
        print(f'Inicializando banco da unidade: {unit_id} ...')
        db_manager.init_database(unit_id)
        print(f'Unidade {unit_id} pronta.')

    print('Todas as bases inicializadas com sucesso.')

if __name__ == '__main__':
    main()
