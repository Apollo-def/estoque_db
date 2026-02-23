# Rotas de Categorias
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from routes.helpers import get_unit_db, admin_required

categories_bp = Blueprint('categories', __name__, url_prefix='/categorias')


@categories_bp.route('')
@admin_required
def categorias():
    if 'unit_id' not in session:
        return redirect(url_for('main.selecionar_unidade'))
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar', 'danger')
        return redirect(url_for('main.selecionar_unidade'))
    cursor = unit_db.execute('SELECT * FROM categorias WHERE ativo = 1 ORDER BY nome')
    return render_template('categorias.html', categorias=cursor.fetchall())


@categories_bp.route('/nova', methods=['GET', 'POST'])
@admin_required
def nova_categoria():
    if 'unit_id' not in session:
        return redirect(url_for('main.selecionar_unidade'))
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar', 'danger')
        return redirect(url_for('main.selecionar_unidade'))
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form.get('descricao', '')
        if not nome:
            flash('Nome obrigatório!', 'danger')
            return render_template('nova_categoria.html')
        try:
            unit_db.execute('INSERT INTO categorias (nome, descricao) VALUES (?, ?)', (nome, descricao))
            unit_db.commit()
            flash('Categoria cadastrada!', 'success')
            return redirect(url_for('categories.categorias'))
        except:
            unit_db.rollback()
            flash('Erro ao cadastrar!', 'danger')
    return render_template('nova_categoria.html')


@categories_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@admin_required
def editar_categoria(id):
    if 'unit_id' not in session:
        return redirect(url_for('main.selecionar_unidade'))
    unit_db = get_unit_db()
    cursor = unit_db.execute('SELECT * FROM categorias WHERE id = ? AND ativo = 1', (id,))
    categoria = cursor.fetchone()
    if not categoria:
        flash('Não encontrada!', 'danger')
        return redirect(url_for('categories.categorias'))
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form.get('descricao', '')
        try:
            unit_db.execute('UPDATE categorias SET nome=?, descricao=? WHERE id=?', (nome, descricao, id))
            unit_db.commit()
            flash('Atualizada!', 'success')
            return redirect(url_for('categories.categorias'))
        except:
            unit_db.rollback()
            flash('Erro!', 'danger')
    return render_template('editar_categoria.html', categoria=categoria)


@categories_bp.route('/excluir/<int:id>')
@admin_required
def excluir_categoria(id):
    if 'unit_id' not in session:
        return redirect(url_for('main.selecionar_unidade'))
    unit_db = get_unit_db()
    try:
        unit_db.execute('UPDATE categorias SET ativo = 0 WHERE id = ?', (id,))
        unit_db.commit()
        flash('Excluída!', 'success')
    except:
        unit_db.rollback()
        flash('Erro!', 'danger')
    return redirect(url_for('categories.categorias'))
