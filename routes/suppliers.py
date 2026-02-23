# Rotas de Fornecedores
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from routes.helpers import get_unit_db, admin_required

suppliers_bp = Blueprint('suppliers', __name__, url_prefix='/fornecedores')


@suppliers_bp.route('')
@admin_required
def fornecedores():
    if 'unit_id' not in session:
        return redirect(url_for('main.selecionar_unidade'))
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar', 'danger')
        return redirect(url_for('main.selecionar_unidade'))
    cursor = unit_db.execute('SELECT * FROM fornecedores WHERE ativo = 1 ORDER BY nome')
    return render_template('fornecedores.html', fornecedores=cursor.fetchall())


@suppliers_bp.route('/novo', methods=['GET', 'POST'])
@admin_required
def novo_fornecedor():
    if 'unit_id' not in session:
        return redirect(url_for('main.selecionar_unidade'))
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar', 'danger')
        return redirect(url_for('main.selecionar_unidade'))
    if request.method == 'POST':
        nome = request.form['nome']
        cnpj = request.form.get('cnpj', '')
        telefone = request.form.get('telefone', '')
        email = request.form.get('email', '')
        endereco = request.form.get('endereco', '')
        if not nome:
            flash('Nome obrigatório!', 'danger')
            return render_template('novo_fornecedor.html')
        try:
            unit_db.execute('INSERT INTO fornecedores (nome, cnpj, telefone, email, endereco) VALUES (?, ?, ?, ?, ?)',
                          (nome, cnpj, telefone, email, endereco))
            unit_db.commit()
            flash('Fornecedor cadastrado!', 'success')
            return redirect(url_for('suppliers.fornecedores'))
        except:
            unit_db.rollback()
            flash('Erro ao cadastrar!', 'danger')
    return render_template('novo_fornecedor.html')


@suppliers_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@admin_required
def editar_fornecedor(id):
    if 'unit_id' not in session:
        return redirect(url_for('main.selecionar_unidade'))
    unit_db = get_unit_db()
    cursor = unit_db.execute('SELECT * FROM fornecedores WHERE id = ? AND ativo = 1', (id,))
    fornecedor = cursor.fetchone()
    if not fornecedor:
        flash('Não encontrado!', 'danger')
        return redirect(url_for('suppliers.fornecedores'))
    if request.method == 'POST':
        nome = request.form['nome']
        cnpj = request.form.get('cnpj', '')
        telefone = request.form.get('telefone', '')
        email = request.form.get('email', '')
        endereco = request.form.get('endereco', '')
        try:
            unit_db.execute('UPDATE fornecedores SET nome=?, cnpj=?, telefone=?, email=?, endereco=? WHERE id=?',
                          (nome, cnpj, telefone, email, endereco, id))
            unit_db.commit()
            flash('Atualizado!', 'success')
            return redirect(url_for('suppliers.fornecedores'))
        except:
            unit_db.rollback()
            flash('Erro!', 'danger')
    return render_template('editar_fornecedor.html', fornecedor=fornecedor)


@suppliers_bp.route('/excluir/<int:id>')
@admin_required
def excluir_fornecedor(id):
    if 'unit_id' not in session:
        return redirect(url_for('main.selecionar_unidade'))
    unit_db = get_unit_db()
    try:
        unit_db.execute('UPDATE fornecedores SET ativo = 0 WHERE id = ?', (id,))
        unit_db.commit()
        flash('Excluído!', 'success')
    except:
        unit_db.rollback()
        flash('Erro!', 'danger')
    return redirect(url_for('suppliers.fornecedores'))
