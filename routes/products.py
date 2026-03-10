# Rotas de Gerenciamento de Produtos
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime, timezone
from routes.helpers import get_unit_db, check_permission, login_required, require_unit

products_bp = Blueprint('products', __name__, url_prefix='/produtos')


@products_bp.route('')
@login_required
@require_unit
def produtos():
    """Lista produtos"""
    from app import db, Usuario
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('main.selecionar_unidade'))
    
    estoque_status = request.args.get('estoque', '')
    
    query = 'SELECT * FROM produtos WHERE ativo = 1'
    params = []
    
    if estoque_status == 'baixo':
        query += ' AND quantidade <= estoque_minimo'
    elif estoque_status == 'zerado':
        query += ' AND quantidade = 0'
    
    query += ' ORDER BY nome'
    
    cursor = unit_db.execute(query, params)
    produtos = cursor.fetchall()
    
    produtos_com_info = []
    for produto in produtos:
        produto_dict = dict(produto)
        if produto_dict.get('usuario_id'):
            try:
                usuario = db.session.get(Usuario, produto_dict['usuario_id'])
                if usuario:
                    produto_dict['usuario_nome'] = usuario.nome
                else:
                    produto_dict['usuario_nome'] = 'Usuário não encontrado'
            except Exception:
                produto_dict['usuario_nome'] = 'Erro ao carregar'
        else:
            produto_dict['usuario_nome'] = None
        produtos_com_info.append(produto_dict)
    
    return render_template('produtos.html', produtos=produtos_com_info)


@products_bp.route('/novo', methods=['GET', 'POST'])
def novo_produto():
    """Criar produto"""
    if 'unit_id' not in session:
        return redirect(url_for('main.selecionar_unidade'))
    
    if not check_permission():
        flash('Acesso negado! Você não tem permissão para cadastrar produtos.', 'danger')
        return redirect(url_for('products.produtos'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('main.selecionar_unidade'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form.get('descricao', '')
        quantidade = int(request.form['quantidade'])
        codigo_barras = request.form.get('codigo_barras', '')
        unidade_medida = request.form.get('unidade_medida', 'un')
        estoque_minimo = int(request.form.get('estoque_minimo', 5))
        
        try:
            cursor = unit_db.execute('''
                INSERT INTO produtos (nome, descricao, quantidade, usuario_id, codigo_barras, unidade_medida, estoque_minimo)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (nome, descricao, quantidade, session['user_id'], codigo_barras, unidade_medida, estoque_minimo))
            unit_db.commit()
            flash('Produto cadastrado com sucesso!', 'success')
            return redirect(url_for('products.produtos'))
        except Exception as e:
            unit_db.rollback()
            flash('Erro ao cadastrar produto!', 'danger')
    
    return render_template('novo_produto.html')


@products_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_produto(id):
    """Editar produto"""
    if 'unit_id' not in session:
        return redirect(url_for('main.selecionar_unidade'))
    
    if not check_permission():
        flash('Acesso negado! Você não tem permissão para editar produtos.', 'danger')
        return redirect(url_for('products.produtos'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('main.selecionar_unidade'))
    
    from app import db, Usuario
    
    cursor = unit_db.execute('SELECT * FROM produtos WHERE id = ? AND ativo = 1', (id,))
    produto = cursor.fetchone()
    
    if not produto:
        flash('Produto não encontrado!', 'danger')
        return redirect(url_for('products.produtos'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form.get('descricao', '')
        quantidade = int(request.form['quantidade'])
        codigo_barras = request.form.get('codigo_barras', '')
        unidade_medida = request.form.get('unidade_medida', 'un')
        estoque_minimo = int(request.form.get('estoque_minimo', 5))
        
        try:
            cursor = unit_db.execute('''
                UPDATE produtos 
                SET nome = ?, descricao = ?, quantidade = ?, 
                    codigo_barras = ?, unidade_medida = ?, estoque_minimo = ?,
                    data_atualizacao = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (nome, descricao, quantidade, codigo_barras, unidade_medida, estoque_minimo, id))
            unit_db.commit()
            flash('Produto atualizado com sucesso!', 'success')
            return redirect(url_for('products.produtos'))
        except Exception as e:
            unit_db.rollback()
            flash('Erro ao atualizar produto!', 'danger')
    
    produto_dict = dict(produto)
    
    if 'usuario_id' in produto_dict and produto_dict['usuario_id']:
        try:
            usuario = db.session.get(Usuario, produto_dict['usuario_id'])
            if usuario:
                produto_dict['usuario'] = {'nome': usuario.nome}
            else:
                produto_dict['usuario'] = {'nome': 'Usuário não encontrado'}
        except Exception as e:
            produto_dict['usuario'] = {'nome': 'Erro ao carregar'}
    else:
        produto_dict['usuario'] = {'nome': 'Não informado'}
    
    for date_field in ['data_criacao', 'data_atualizacao']:
        if date_field in produto_dict and produto_dict[date_field]:
            if isinstance(produto_dict[date_field], str):
                try:
                    data_str = produto_dict[date_field]
                    if 'T' in data_str:
                        produto_dict[date_field] = datetime.fromisoformat(data_str.replace('T', ' ').replace('Z', ''))
                    else:
                        produto_dict[date_field] = datetime.strptime(data_str, '%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    produto_dict[date_field] = datetime.now()
    
    return render_template('editar_produto.html', produto=produto_dict)


@products_bp.route('/excluir/<int:id>')
def excluir_produto(id):
    """Excluir produto"""
    if 'unit_id' not in session:
        return redirect(url_for('main.selecionar_unidade'))
    
    from app import db, Usuario
    
    # Verificar se é admin
    usuario = db.session.get(Usuario, session['user_id'])
    if not usuario or usuario.tipo != 'admin':
        flash('Acesso negado! Apenas administradores podem excluir produtos.', 'danger')
        return redirect(url_for('products.produtos'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('main.selecionar_unidade'))
    
    try:
        cursor = unit_db.execute('UPDATE produtos SET ativo = 0 WHERE id = ?', (id,))
        unit_db.commit()
        flash('Produto excluído com sucesso!', 'success')
    except Exception as e:
        unit_db.rollback()
        flash('Erro ao excluir produto!', 'danger')
    
    return redirect(url_for('products.produtos'))
