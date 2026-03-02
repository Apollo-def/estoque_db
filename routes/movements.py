# Rotas de Movimentações
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from routes.helpers import get_unit_db, check_permission

movements_bp = Blueprint('movements', __name__, url_prefix='/movimentacoes')


@movements_bp.route('')
def movimentacoes():
    """Lista movimentações"""
    from app import db, Usuario
    
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if 'unit_id' not in session:
        return redirect(url_for('main.selecionar_unidade'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('main.selecionar_unidade'))
    
    tipo = request.args.get('tipo', '')
    produto_id = request.args.get('produto_id', '')
    setor = request.args.get('setor', '')
    
    # Build query dynamically
    query = '''
        SELECT m.*, p.nome as produto_nome
        FROM movimentacoes m
        LEFT JOIN produtos p ON m.produto_id = p.id
        WHERE 1=1
    '''
    params = []
    
    if tipo:
        query += ' AND m.tipo = ?'
        params.append(tipo)
    
    if produto_id:
        query += ' AND m.produto_id = ?'
        params.append(produto_id)
    
    if setor:
        query += ' AND (m.origem LIKE ? OR m.destino LIKE ?)'
        params.append(f'%{setor}%')
        params.append(f'%{setor}%')
    
    query += ' ORDER BY m.data_movimentacao DESC'
    
    cursor = unit_db.execute(query, params)
    movimentacoes = cursor.fetchall()
    
    movimentacoes_com_info = []
    for mov in movimentacoes:
        mov_dict = dict(mov)
        
        if mov_dict.get('usuario_responsavel_id'):
            try:
                usuario = db.session.get(Usuario, mov_dict['usuario_responsavel_id'])
                if usuario:
                    mov_dict['usuario_responsavel'] = {'nome': usuario.nome}
                else:
                    mov_dict['usuario_responsavel'] = {'nome': 'Usuário não encontrado'}
            except Exception:
                mov_dict['usuario_responsavel'] = {'nome': 'Erro ao carregar'}
        else:
            mov_dict['usuario_responsavel'] = {'nome': 'Não informado'}
        
        movimentacoes_com_info.append(mov_dict)
    
    cursor = unit_db.execute('SELECT id, nome, quantidade FROM produtos WHERE ativo = 1 ORDER BY nome')
    produtos = cursor.fetchall()
    
    # Get unique setores from movimentacoes (origem and destino)
    cursor = unit_db.execute('''
        SELECT DISTINCT COALESCE(origem, destino) as nome 
        FROM movimentacoes 
        WHERE origem IS NOT NULL OR destino IS NOT NULL
        ORDER BY nome
    ''')
    setores = [row['nome'] for row in cursor.fetchall()]
    
    cursor = unit_db.execute('SELECT SUM(quantidade) as total FROM produtos WHERE ativo = 1')
    saldo_geral = cursor.fetchone()[0] or 0
    
    return render_template('movimentacoes.html', 
                         movimentacoes=movimentacoes_com_info, 
                         produtos=produtos,
                         setores=setores,
                         saldo_geral=saldo_geral)


@movements_bp.route('/entrada', methods=['GET', 'POST'])
def entrada_produto():
    """Registrar entrada de produto"""
    if 'unit_id' not in session:
        return redirect(url_for('main.selecionar_unidade'))
    
    if not check_permission():
        flash('Acesso negado! Você não tem permissão para movimentar produtos.', 'danger')
        return redirect(url_for('movements.movimentacoes'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('main.selecionar_unidade'))
    
    if request.method == 'POST':
        produto_id = request.form['produto_id']
        quantidade = int(request.form['quantidade'])
        origem = request.form.get('origem', '')
        nota_fiscal = request.form.get('nota_fiscal', '')
        motivo = request.form.get('motivo', '')
        
        cursor = unit_db.execute('SELECT * FROM produtos WHERE id = ? AND ativo = 1', (produto_id,))
        produto = cursor.fetchone()
        
        if not produto:
            flash('Produto não encontrado!', 'danger')
            produtos = unit_db.execute('SELECT id, nome FROM produtos WHERE ativo = 1 ORDER BY nome').fetchall()
            return render_template('entrada_produto.html', produtos=produtos)
        
        try:
            cursor = unit_db.execute('''
                INSERT INTO movimentacoes (produto_id, tipo, quantidade, usuario_responsavel_id, origem, nota_fiscal, motivo)
                VALUES (?, 'entrada', ?, ?, ?, ?, ?)
            ''', (produto_id, quantidade, session['user_id'], origem, nota_fiscal, motivo))
            
            cursor = unit_db.execute('UPDATE produtos SET quantidade = quantidade + ?, data_atualizacao = CURRENT_TIMESTAMP WHERE id = ?', 
                                    (quantidade, produto_id))
            
            unit_db.commit()
            flash(f'Entrada de {quantidade} unidades de {produto["nome"]} registrada com sucesso!', 'success')
            return redirect(url_for('movements.movimentacoes'))
        except Exception as e:
            unit_db.rollback()
            flash('Erro ao registrar entrada!', 'danger')
    
    produtos = unit_db.execute('SELECT id, nome FROM produtos WHERE ativo = 1 ORDER BY nome').fetchall()
    return render_template('entrada_produto.html', produtos=produtos)


@movements_bp.route('/saida', methods=['GET', 'POST'])
def saida_produto():
    """Registrar saída de produto"""
    if 'unit_id' not in session:
        return redirect(url_for('main.selecionar_unidade'))
    
    if not check_permission():
        flash('Acesso negado! Você não tem permissão para movimentar produtos.', 'danger')
        return redirect(url_for('movements.movimentacoes'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('main.selecionar_unidade'))
    
    if request.method == 'POST':
        produto_id = request.form['produto_id']
        quantidade = int(request.form['quantidade'])
        destino = request.form.get('destino', '')
        # Reutilizamos a coluna ordem_servico para salvar o nome do responsável
        ordem_servico = request.form.get('responsavel_retirada', '')
        motivo = request.form.get('motivo', '')
        
        cursor = unit_db.execute('SELECT * FROM produtos WHERE id = ? AND ativo = 1', (produto_id,))
        produto = cursor.fetchone()
        
        if not produto:
            flash('Produto não encontrado!', 'danger')
            produtos = unit_db.execute('SELECT id, nome, quantidade FROM produtos WHERE ativo = 1 ORDER BY nome').fetchall()
            setores = unit_db.execute('SELECT id, nome FROM setores WHERE ativo = 1 ORDER BY nome').fetchall()
            return render_template('saida_produto.html', produtos=produtos, setores=setores)
        
        if produto['quantidade'] < quantidade:
            flash(f'Estoque insuficiente! Produto tem apenas {produto["quantidade"]} unidades.', 'danger')
            produtos = unit_db.execute('SELECT id, nome, quantidade FROM produtos WHERE ativo = 1 ORDER BY nome').fetchall()
            setores = unit_db.execute('SELECT id, nome FROM setores WHERE ativo = 1 ORDER BY nome').fetchall()
            return render_template('saida_produto.html', produtos=produtos, setores=setores)
        
        try:
            cursor = unit_db.execute('UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?', (quantidade, produto_id))
            
            cursor = unit_db.execute('''
                INSERT INTO movimentacoes (produto_id, tipo, quantidade, usuario_responsavel_id, destino, ordem_servico, motivo)
                VALUES (?, 'saida', ?, ?, ?, ?, ?)
            ''', (produto_id, quantidade, session['user_id'], destino, ordem_servico, motivo))
            
            unit_db.commit()
            flash(f'Saída de {quantidade} unidades de {produto["nome"]} registrada com sucesso!', 'success')
            return redirect(url_for('movements.movimentacoes'))
        except Exception as e:
            unit_db.rollback()
            flash('Erro ao registrar saída!', 'danger')
    
    produtos = unit_db.execute('SELECT id, nome, quantidade FROM produtos WHERE ativo = 1 ORDER BY nome').fetchall()
    setores = unit_db.execute('SELECT id, nome FROM setores WHERE ativo = 1 ORDER BY nome').fetchall()
    return render_template('saida_produto.html', produtos=produtos, setores=setores)


@movements_bp.route('/excluir/<int:id>')
def excluir_movimentacao(id):
    """Excluir movimentação"""
    if 'unit_id' not in session:
        return redirect(url_for('main.selecionar_unidade'))
    
    if not check_permission():
        flash('Acesso negado! Você não tem permissão para excluir movimentações.', 'danger')
        return redirect(url_for('movements.movimentacoes'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('main.selecionar_unidade'))
    
    try:
        cursor = unit_db.execute('SELECT * FROM movimentacoes WHERE id = ?', (id,))
        movimentacao = cursor.fetchone()
        
        if not movimentacao:
            flash('Movimentação não encontrada!', 'danger')
            return redirect(url_for('movements.movimentacoes'))
        
        cursor = unit_db.execute('SELECT * FROM produtos WHERE id = ?', (movimentacao['produto_id'],))
        produto = cursor.fetchone()
        
        if produto:
            if movimentacao['tipo'] == 'entrada':
                nova_quantidade = produto['quantidade'] - movimentacao['quantidade']
            else:
                nova_quantidade = produto['quantidade'] + movimentacao['quantidade']
            
            cursor = unit_db.execute('UPDATE produtos SET quantidade = ? WHERE id = ?', (nova_quantidade, movimentacao['produto_id']))
        
        cursor = unit_db.execute('DELETE FROM movimentacoes WHERE id = ?', (id,))
        unit_db.commit()
        flash('Movimentação excluída e estoque atualizado!', 'success')
    except Exception as e:
        unit_db.rollback()
        flash('Erro ao excluir movimentação!', 'danger')
    
    return redirect(url_for('movements.movimentacoes'))
