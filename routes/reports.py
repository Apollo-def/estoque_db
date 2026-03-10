# routes/reports.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from routes.helpers import login_required, require_unit, get_unit_db

reports_bp = Blueprint('reports', __name__, url_prefix='/relatorios')

@reports_bp.route('/geral')
@login_required
@require_unit
def relatorio_geral():
    # Verifica se o usuário tem permissão para ver relatórios
    if not session.get('permissoes_menu', {}).get('relatorios', False):
        flash('Acesso negado. Você não tem permissão para ver relatórios.', 'danger')
        return redirect(url_for('main.index'))

    unit_db = get_unit_db()
    if not unit_db:
        flash('Erro ao conectar com o banco da unidade', 'danger')
        return redirect(url_for('main.selecionar_unidade'))

    try:
        # Métricas gerais
        cursor = unit_db.execute('SELECT COUNT(id) FROM produtos WHERE ativo = 1')
        total_produtos_distintos = cursor.fetchone()[0] or 0
        
        cursor = unit_db.execute('SELECT SUM(quantidade) FROM produtos WHERE ativo = 1')
        total_itens_estoque = cursor.fetchone()[0] or 0

        # Produtos com estoque baixo
        cursor = unit_db.execute('SELECT * FROM produtos WHERE ativo = 1 AND quantidade > 0 AND quantidade <= estoque_minimo ORDER BY quantidade ASC')
        produtos_estoque_baixo = cursor.fetchall()

        # Produtos com estoque zerado
        cursor = unit_db.execute('SELECT * FROM produtos WHERE ativo = 1 AND quantidade = 0 ORDER BY nome ASC')
        produtos_estoque_zerado = cursor.fetchall()
    except Exception as e:
        flash(f'Erro ao gerar o relatório: {e}', 'danger')
        return redirect(url_for('main.index'))

    return render_template('relatorio_geral.html',
                           total_produtos_distintos=total_produtos_distintos,
                           total_itens_estoque=total_itens_estoque,
                           produtos_estoque_baixo=produtos_estoque_baixo,
                           produtos_estoque_zerado=produtos_estoque_zerado)