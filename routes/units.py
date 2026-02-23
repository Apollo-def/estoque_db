# Rotas de Gerenciamento de Unidades
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import os
import re
import shutil
from datetime import datetime, timezone
from routes.helpers import admin_required

units_bp = Blueprint('units', __name__, url_prefix='/unidades')


@units_bp.route('')
def listar_unidades():
    """Lista todas as unidades"""
    from app import db, Usuario, Unidade
    
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if session.get('user_tipo') == 'admin':
        unidades = Unidade.query.order_by(Unidade.id).all()
        return render_template('listar_unidades.html', unidades=unidades)
    
    user_permissoes = session.get('permissoes_menu', {})
    
    if not user_permissoes.get('unidades', False):
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('main.index'))
    
    unidades = Unidade.query.order_by(Unidade.id).all()
    return render_template('listar_unidades.html', unidades=unidades)


@units_bp.route('/novo', methods=['GET', 'POST'])
@admin_required
def novo_unidade():
    """Criar nova unidade"""
    from app import db, Unidade
    from database_config import DATABASES
    from database_manager import db_manager
    
    if request.method == 'POST':
        unit_id = request.form.get('unit_id', '').strip()
        nome = request.form.get('nome', '').strip()
        descricao = request.form.get('descricao', '').strip()
        arquivo_db = request.form.get('arquivo_db', '').strip()

        if not unit_id or not nome or not arquivo_db:
            flash('Preencha id, nome e arquivo do banco (database).', 'danger')
            return render_template('novo_unidade.html')

        if not re.match(r'^[a-zA-Z0-9_\-]+$', unit_id):
            flash('Id da unidade inválido. Use letras, números, traço ou underscore.', 'danger')
            return render_template('novo_unidade.html')

        if unit_id in DATABASES:
            flash('Já existe uma unidade com este id.', 'danger')
            return render_template('novo_unidade.html')

        try:
            conn = db_manager.get_connection(None)
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(unidades)")
            cols = [r['name'] for r in cur.fetchall()]
            if 'database' not in cols:
                cur.execute("ALTER TABLE unidades ADD COLUMN database TEXT")
            if 'type' not in cols:
                cur.execute("ALTER TABLE unidades ADD COLUMN type TEXT")
            conn.commit()
        except Exception:
            pass

        if db.session.get(Unidade, unit_id):
            flash('Já existe uma unidade com este id na base central.', 'danger')
            return render_template('novo_unidade.html')

        try:
            nova = Unidade(id=unit_id, nome=nome, descricao=descricao, database=arquivo_db, type='sqlite')
            db.session.add(nova)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash('Erro ao salvar unidade no banco central.', 'danger')
            return render_template('novo_unidade.html')

        DATABASES[unit_id] = {
            'name': nome,
            'database': arquivo_db,
            'host': 'localhost',
            'type': 'sqlite',
            'description': descricao
        }

        try:
            db_manager.init_database(unit_id)
            flash('Unidade criada com sucesso e banco inicializado.', 'success')
            return redirect(url_for('users.tabela'))
        except Exception as e:
            flash('Unidade criada no central, mas falha ao inicializar o banco.', 'warning')
            return redirect(url_for('users.tabela'))

    return render_template('novo_unidade.html')


@units_bp.route('/editar/<unit_id>', methods=['GET', 'POST'])
@admin_required
def editar_unidade(unit_id):
    """Editar unidade"""
    from app import db, Unidade
    from database_config import DATABASES
    
    unidade = Unidade.query.get_or_404(unit_id)
    
    # Get db_path for file operations
    from app import db_path

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        descricao = request.form.get('descricao', '').strip()
        arquivo_db = request.form.get('arquivo_db', '').strip()
        ativa = 1 if request.form.get('ativa') == 'on' else 0

        if not nome or not arquivo_db:
            flash('Nome e arquivo do banco são obrigatórios.', 'danger')
            return render_template('editar_unidade.html', unidade=unidade)

        old_file = unidade.database or ''
        new_file = arquivo_db
        try:
            if old_file and old_file != new_file:
                old_path = os.path.join(os.path.dirname(db_path), old_file)
                new_path = os.path.join(os.path.dirname(db_path), new_file)
                if os.path.exists(old_path) and not os.path.exists(new_path):
                    os.rename(old_path, new_path)
        except Exception as e:
            flash('Unidade atualizada, mas falha ao renomear arquivo.', 'warning')

        unidade.nome = nome
        unidade.descricao = descricao
        unidade.database = arquivo_db
        unidade.ativa = ativa
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash('Erro ao salvar alterações.', 'danger')
            return render_template('editar_unidade.html', unidade=unidade)

        DATABASES[unit_id] = {
            'name': unidade.nome,
            'database': unidade.database,
            'host': 'localhost',
            'type': unidade.type or 'sqlite',
            'description': unidade.descricao
        }

        flash('Unidade atualizada com sucesso.', 'success')
        return redirect(url_for('users.tabela'))

    return render_template('editar_unidade.html', unidade=unidade)


@units_bp.route('/excluir/<unit_id>', methods=['GET', 'POST'])
@admin_required
def excluir_unidade(unit_id):
    """Excluir unidade"""
    from app import db, Unidade, Usuario
    from database_config import DATABASES
    import json
    
    unidade = Unidade.query.get_or_404(unit_id)
    from app import db_path
    
    if request.method == 'POST':
        arquivo = unidade.database or ''
        instance_dir = os.path.dirname(db_path)
        try:
            if arquivo:
                src = os.path.join(instance_dir, arquivo)
                if os.path.exists(src):
                    backups_dir = os.path.join(instance_dir, 'backups')
                    os.makedirs(backups_dir, exist_ok=True)
                    ts = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
                    dst = os.path.join(backups_dir, f"{unit_id}_{ts}.db")
                    shutil.copy2(src, dst)

                    if request.form.get('remover_arquivo') == 'on':
                        try:
                            os.remove(src)
                        except Exception:
                            pass

            db.session.delete(unidade)

            usuarios = Usuario.query.all()
            for u in usuarios:
                try:
                    unidades = u.get_unidades_acesso()
                    if unit_id in unidades:
                        unidades.remove(unit_id)
                        u.unidades_acesso = json.dumps(unidades) if unidades else None
                except Exception:
                    pass

            db.session.commit()

            if unit_id in DATABASES:
                del DATABASES[unit_id]

            flash('Unidade excluída. Backup criado em instance/backups/.', 'success')
            return redirect(url_for('users.tabela'))

        except Exception as e:
            db.session.rollback()
            flash('Erro ao excluir unidade.', 'danger')
            return redirect(url_for('users.tabela'))

    return render_template('confirmar_excluir_unidade.html', unidade=unidade)
