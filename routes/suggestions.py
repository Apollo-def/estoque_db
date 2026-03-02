# routes/suggestions.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime, timezone
from routes.helpers import login_required
from models import db, Sugestao, Usuario, Notificacao

suggestions_bp = Blueprint('suggestions', __name__, url_prefix='/sugestoes')

# Rota para usuários verem suas próprias sugestões e criarem novas
@suggestions_bp.route('/')
@login_required
def minhas_sugestoes():
    user_id = session['user_id']
    sugestoes = Sugestao.query.filter_by(usuario_id=user_id).order_by(Sugestao.data_criacao.desc()).all()
    return render_template('minhas_sugestoes.html', sugestoes=sugestoes)

# Rota para criar uma nova sugestão
@suggestions_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova_sugestao():
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descricao = request.form.get('descricao')

        if not titulo or not descricao:
            flash('Título e descrição são obrigatórios.', 'danger')
            return render_template('nova_sugestao.html')

        nova = Sugestao(
            usuario_id=session['user_id'],
            titulo=titulo,
            descricao=descricao
        )
        db.session.add(nova)
        db.session.commit()

        # Notificar todos os administradores
        try:
            admins = Usuario.query.filter_by(tipo='admin').all()
            autor = Usuario.query.get(session['user_id'])
            for admin in admins:
                notificacao = Notificacao(
                    usuario_id=admin.id,
                    mensagem=f"Nova sugestão de {autor.nome}: '{nova.titulo[:30]}...'",
                    link=url_for('suggestions.responder_sugestao', id=nova.id)
                )
                db.session.add(notificacao)
            db.session.commit()
        except Exception as e:
            db.session.rollback()

        flash('Sua sugestão foi enviada com sucesso! Obrigado por sua contribuição.', 'success')
        return redirect(url_for('suggestions.minhas_sugestoes'))

    return render_template('nova_sugestao.html')

# Rota para admin ver todas as sugestões
@suggestions_bp.route('/admin')
@login_required
def admin_sugestoes():
    if session.get('user_tipo') != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))

    sugestoes = Sugestao.query.order_by(Sugestao.data_criacao.desc()).all()
    return render_template('admin_sugestoes.html', sugestoes=sugestoes)

# Rota para admin responder uma sugestão
@suggestions_bp.route('/admin/responder/<int:id>', methods=['GET', 'POST'])
@login_required
def responder_sugestao(id):
    if session.get('user_tipo') != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))

    sugestao = Sugestao.query.get_or_404(id)

    if request.method == 'POST':
        status = request.form.get('status')
        resposta = request.form.get('resposta_admin')

        sugestao.status = status
        sugestao.resposta_admin = resposta
        sugestao.data_resposta = datetime.now(timezone.utc)

        # Notificar o usuário sobre a resposta
        notificacao = Notificacao(
            usuario_id=sugestao.usuario_id,
            mensagem=f"Sua sugestão '{sugestao.titulo[:20]}...' foi respondida.",
            link=url_for('suggestions.minhas_sugestoes')
        )
        db.session.add(notificacao)

        db.session.commit()
        flash('Resposta enviada com sucesso!', 'success')
        return redirect(url_for('suggestions.admin_sugestoes'))

    return render_template('responder_sugestao.html', sugestao=sugestao)