# Rotas de Setores
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from routes.helpers import get_unit_db, admin_required

sectors_bp = Blueprint('sectors', __name__, url_prefix='/setores')


@sectors_bp.route('')
@admin_required
def setores():
    if 'unit_id' not in session:
        return redirect(url_for('main.selecionar_unidade'))
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar', 'danger')
        return redirect(url_for('main.selecionar_unidade'))
    cursor = unit_db.execute('SELECT * FROM setores WHERE ativo = 1 ORDER BY nome')
    return render_template('setores.html', setores=cursor.fetchall())


@sectors_bp.route('/novo', methods=['GET', 'POST'])
@admin_required
def novo_setor():
    if 'unit_id' not in session:
        return redirect(url_for('main.selecionar_unidade'))
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar', 'danger')
        return redirect(url_for('main.selecionar_unidade'))
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form.get('descricao', '')
        responsavel = request.form.get('responsavel', '')
        if not nome:
            flash('Nome obrigatório!', 'danger')
            return render_template('novo_setor.html')
        try:
            unit_db.execute('INSERT INTO setores (nome, descricao, responsavel) VALUES (?, ?, ?)',
                          (nome, descricao, responsavel))
            unit_db.commit()
            flash('Setor cadastrado!', 'success')
            return redirect(url_for('sectors.setores'))
        except:
            unit_db.rollback()
            flash('Erro ao cadastrar!', 'danger')
    return render_template('novo_setor.html')


@sectors_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@admin_required
def editar_setor(id):
    if 'unit_id' not in session:
        return redirect(url_for('main.selecionar_unidade'))
    unit_db = get_unit_db()
    cursor = unit_db.execute('SELECT * FROM setores WHERE id = ? AND ativo = 1', (id,))
    setor = cursor.fetchone()
    if not setor:
        flash('Não encontrado!', 'danger')
        return redirect(url_for('sectors.setores'))
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form.get('descricao', '')
        responsavel = request.form.get('responsavel', '')
        try:
            unit_db.execute('UPDATE setores SET nome=?, descricao=?, responsavel=? WHERE id=?',
                          (nome, descricao, responsavel, id))
            unit_db.commit()
            flash('Atualizado!', 'success')
            return redirect(url_for('sectors.setores'))
        except:
            unit_db.rollback()
            flash('Erro!', 'danger')
    return render_template('editar_setor.html', setor=setor)


@sectors_bp.route('/excluir/<int:id>')
@admin_required
def excluir_setor(id):
    if 'unit_id' not in session:
        return redirect(url_for('main.selecionar_unidade'))
    unit_db = get_unit_db()
    try:
        unit_db.execute('UPDATE setores SET ativo = 0 WHERE id = ?', (id,))
        unit_db.commit()
        flash('Excluído!', 'success')
    except:
        unit_db.rollback()
        flash('Erro!', 'danger')
    return redirect(url_for('sectors.setores'))
