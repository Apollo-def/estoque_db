# routes/system.py
from flask import Blueprint, current_app, send_from_directory, flash, redirect, url_for, session, request
from routes.helpers import admin_required, login_required
import os
import zipfile
from datetime import datetime
from models import db, Notificacao

system_bp = Blueprint('system', __name__, url_prefix='/sistema')

@system_bp.route('/backup')
@admin_required
def create_backup():
    """Cria um backup ZIP de toda a pasta 'instance' e o oferece para download."""
    try:
        # Caminho para a pasta 'instance'
        instance_path = os.path.join(current_app.root_path, 'instance')
        
        # Caminho para a pasta de backups temporários (será criada se não existir)
        backup_dir = os.path.join(current_app.root_path, 'temp_backups')
        os.makedirs(backup_dir, exist_ok=True)

        # Nome do arquivo de backup com data e hora
        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        backup_filename = f'backup_completo_{timestamp}.zip'
        backup_filepath = os.path.join(backup_dir, backup_filename)

        # Cria o arquivo ZIP com todos os dados da pasta 'instance'
        with zipfile.ZipFile(backup_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(instance_path):
                # Evita incluir a subpasta de backups (se existir) dentro do novo backup
                if 'backups' in dirs:
                    dirs.remove('backups')
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, instance_path)
                    zipf.write(file_path, arcname)
        
        return send_from_directory(directory=backup_dir, path=backup_filename, as_attachment=True)

    except Exception as e:
        current_app.logger.error(f"Falha ao criar backup: {e}")
        flash('Ocorreu um erro ao gerar o arquivo de backup.', 'danger')
        return redirect(url_for('main.index'))


@system_bp.route('/notifications/read/<int:id>')
@login_required
def read_notification(id):
    """Marca uma notificação como lida e redireciona para o link."""
    notificacao = Notificacao.query.get_or_404(id)
    
    if notificacao.usuario_id != session['user_id']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
        
    notificacao.lida = True
    db.session.commit()
    
    if notificacao.link:
        return redirect(notificacao.link)
    
    return redirect(url_for('main.index'))


@system_bp.route('/notifications/read-all')
@login_required
def mark_all_notifications_as_read():
    """Marca todas as notificações do usuário como lidas."""
    try:
        Notificacao.query.filter_by(usuario_id=session['user_id'], lida=False).update({'lida': True})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao marcar notificações como lidas: {e}")
    return redirect(request.referrer or url_for('main.index'))