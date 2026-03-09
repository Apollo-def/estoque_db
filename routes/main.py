# Rotas Principais - Dashboard e Seleção de Unidade
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from routes.helpers import get_unit_db

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Página principal - Dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if 'unit_id' not in session:
        return redirect(url_for('main.selecionar_unidade'))
    
    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('main.selecionar_unidade'))
    
    # Estatísticas
    cursor = unit_db.execute('SELECT COUNT(*) FROM produtos WHERE ativo = 1')
    total_produtos = cursor.fetchone()[0]
    
    cursor = unit_db.execute('SELECT COUNT(*) FROM produtos WHERE ativo = 1 AND quantidade <= estoque_minimo')
    produtos_baixo_estoque = cursor.fetchone()[0]
    
    cursor = unit_db.execute('SELECT COUNT(*) FROM movimentacoes WHERE tipo = "entrada"')
    total_entradas = cursor.fetchone()[0]
    
    cursor = unit_db.execute('SELECT COUNT(*) FROM movimentacoes WHERE tipo = "saida"')
    total_saidas = cursor.fetchone()[0]
    
    # Movimentações recentes
    cursor = unit_db.execute('''
        SELECT m.*, p.nome as produto_nome
        FROM movimentacoes m
        JOIN produtos p ON m.produto_id = p.id
        WHERE p.ativo = 1
        ORDER BY m.data_movimentacao DESC
        LIMIT 5
    ''')
    movimentacoes_recentes = cursor.fetchall()
    
    from database_config import get_database_config
    unit_config = get_database_config(session['unit_id'])
    
    return render_template('index.html', 
                         total_produtos=total_produtos,
                         produtos_baixo_estoque=produtos_baixo_estoque,
                         total_entradas=total_entradas,
                         total_saidas=total_saidas,
                         movimentacoes_recentes=movimentacoes_recentes,
                         unidade_atual=unit_config)


@main_bp.route('/selecionar-unidade', methods=['GET', 'POST'])
def selecionar_unidade():
    """Seleção de unidade"""
    from app import db, Usuario
    from database_config import get_database_config, get_all_units
    from database_manager import db_manager
    
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        unit_id = request.form.get('unit_id')
        usuario = db.session.get(Usuario, session['user_id'])
        
        if not usuario.pode_acessar_unidade(unit_id):
            flash('Você não tem permissão para acessar esta unidade', 'danger')
            return redirect(url_for('main.selecionar_unidade'))
        
        unit_config = get_database_config(unit_id)
        if not unit_config:
            flash('Unidade não encontrada', 'danger')
            return redirect(url_for('main.selecionar_unidade'))
        
        try:
            unit_db = db_manager.get_connection(unit_id)
            session['unit_id'] = unit_id
            session['unit_name'] = unit_config['name']
            flash(f'Bem-vindo à {unit_config["name"]}!', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            flash('Erro ao conectar com a unidade', 'danger')
            return redirect(url_for('main.selecionar_unidade'))
    
    usuario = db.session.get(Usuario, session['user_id'])
    
    if usuario.is_admin():
        unidades = get_all_units()
    else:
        unidades_permitidas = usuario.get_unidades_acesso()
        todas_unidades = get_all_units()
        unidades = {k: v for k, v in todas_unidades.items() if k in unidades_permitidas}
    
    # Se não houver unidades e for admin, redirecionar para criar uma
    if not unidades and usuario.is_admin():
        flash('Nenhuma unidade encontrada. Por favor, crie a primeira unidade do sistema.', 'info')
        return redirect(url_for('units.novo_unidade'))
    
    return render_template('selecionar_unidade.html', unidades=unidades)


@main_bp.route('/trocar-unidade')
def trocar_unidade():
    """Remove unidade da sessão e redireciona para seleção ou alterna para outra unidade"""
    from app import db, Usuario
    from database_config import get_database_config, get_all_units
    from database_manager import db_manager
    
    # Verificar se quer trocar para uma unidade específica
    proxima_unidade = request.args.get('proxima')
    
    if proxima_unidade:
        # Trocar para a unidade especificada
        usuario = db.session.get(Usuario, session['user_id'])
        
        if not usuario.pode_acessar_unidade(proxima_unidade):
            flash('Você não tem permissão para acessar esta unidade', 'danger')
            return redirect(url_for('main.selecionar_unidade'))
        
        unit_config = get_database_config(proxima_unidade)
        if not unit_config:
            flash('Unidade não encontrada', 'danger')
            return redirect(url_for('main.selecionar_unidade'))
        
        try:
            # Verificar se o banco da unidade existe
            unit_db = db_manager.get_connection(proxima_unidade)
            session['unit_id'] = proxima_unidade
            session['unit_name'] = unit_config['name']
            flash(f'Unidade alterada para {unit_config["name"]}!', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            flash('Erro ao conectar com a unidade', 'danger')
            return redirect(url_for('main.selecionar_unidade'))
    
    # Se não especificou unidade, apenas remove a atual e redireciona para seleção
    if 'unit_id' in session:
        del session['unit_id']
    if 'unit_name' in session:
        del session['unit_name']
    return redirect(url_for('main.selecionar_unidade'))
