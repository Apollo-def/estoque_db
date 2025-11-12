// SPA Navigation and API Integration for Almoxarifado

document.addEventListener('DOMContentLoaded', () => {
  // Check if user is logged in
  const user = localStorage.getItem('user');
  if (!user) {
    window.location.href = 'login.html';
    return;
  }

  const userData = JSON.parse(user);
  const userRole = userData.role;
  const userName = userData.username;

  // Cache DOM elements
  // Seleciona apenas os links do menu principal (primeira .nav-links dentro da sidebar)
  const sidebar = document.querySelector('.sidebar');
  const mainNav = sidebar ? (sidebar.querySelectorAll('.nav-links')[0]) : null;
  const navLinks = mainNav ? mainNav.querySelectorAll('a') : document.querySelectorAll('.nav-links a');
  const mainContent = document.querySelector('.main-content');
  const usuariosSection = document.getElementById('usuarios-section');
  const usersTableBody = document.getElementById('users-table-body');
  const addUserBtn = document.getElementById('add-user-btn');
  const productTableBody = document.getElementById('product-table-body');
  const prevBtn = document.querySelector('.pagination button:first-child');
  const nextBtn = document.querySelector('.pagination button:last-child');
  const currentPageSpan = document.querySelector('.pagination .current-page');
  const searchInput = document.querySelector('.search-input input');
  const movimentacoesSection = document.getElementById('movimentacoes-section');
  const movimentacoesTableBody = document.getElementById('movimentacoes-table-body');
  const addMovementBtn = document.getElementById('add-movement-btn');
  const movimentacaoForm = document.getElementById('movimentacao-form');
  const movProduto = document.getElementById('mov-produto');
  const movTipo = document.getElementById('mov-tipo');
  const movQuantidade = document.getElementById('mov-quantidade');
  const movLocal = document.getElementById('mov-local');
  const movObservacoes = document.getElementById('mov-observacoes');
  const resumoQtdAtual = document.getElementById('resumo-qtd-atual');
  const resumoQtdMinima = document.getElementById('resumo-qtd-minima');
  const resumoLocal = document.getElementById('resumo-local');
  const resumoCategoria = document.getElementById('resumo-categoria');
  const configuracoesSection = document.getElementById('configuracoes-section');
  const relatoriosSection = document.getElementById('relatorios-section');
  const addProductBtn = document.querySelector('.header-buttons .btn:first-child');
  const exportBtn = document.querySelector('.header-buttons .btn:last-child');
  const quickActionBtns = document.querySelectorAll('.sidebar-right .quick-action-btn');
  const quickActionLink = document.querySelector('.sidebar-right .quick-action-link');
  const vendasTableBody = document.getElementById('vendas-table-body');

  let currentPage = 1;
  const itemsPerPage = 10;
  let products = [];
  let filteredProducts = [];
  let charts = {};

  // Mostrar/Ocultar Relatórios baseado na role
  function updateNavigation() {
    const relatorioLink = Array.from(navLinks).find(l => l.textContent.trim() === 'Relatórios');
    if (relatorioLink) {
      if (userRole === 'admin') {
        relatorioLink.style.display = 'flex';
      } else {
        relatorioLink.style.display = 'none';
      }
    }
  }
  updateNavigation();

  // Navigation menu click handler
  if (navLinks) {
    navLinks.forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      navLinks.forEach(l => l.classList.remove('active'));
      link.classList.add('active');
      const section = link.textContent.trim();

      // Hide all sections
      mainContent.style.display = 'none';
      usuariosSection.style.display = 'none';
      movimentacoesSection.style.display = 'none';
      configuracoesSection.style.display = 'none';
      if (relatoriosSection) relatoriosSection.style.display = 'none';

      if (section === 'Produtos') {
        mainContent.style.display = 'flex';
        fetchProducts();
      } else if (section === 'Usuários') {
        usuariosSection.style.display = 'block';
        fetchUsers();
      } else if (section === 'Movimentações') {
        movimentacoesSection.style.display = 'block';
        fetchMovimentacoes();
        clearMovimentacaoForm();
      } else if (section === 'Relatórios') {
        relatoriosSection.style.display = 'block';
        fetchRelatorios();
      } else if (section === 'Configurações') {
        configuracoesSection.style.display = 'block';
      } else if (section === 'Exportar Dados') {
        exportData();
      } else {
        alert(`Seção "${section}" ainda não implementada.`);
      }
    });
    });
  }

  if (navLinks && navLinks.length > 0) navLinks[0].click();

  // ==================================================
  // Handlers específicos para opções dentro de Relatórios
  // ==================================================
  const relVendasLink = document.querySelector('.relatorio-vendas');
  const relEstoqueLink = document.querySelector('.relatorio-estoque');
  const relValidadeLink = document.querySelector('.relatorio-validade');
  const relFinanceiroLink = document.querySelector('.relatorio-financeiro');
  const relExportLink = document.querySelector('.exportar');

  // Container dinâmico para conteúdo de relatórios (criado se não existir)
  function getReportContainer() {
    let container = document.getElementById('report-content');
    if (!container && relatoriosSection) {
      container = document.createElement('div');
      container.id = 'report-content';
      container.style.marginTop = '1.5rem';
      relatoriosSection.appendChild(container);
    }
    return container;
  }

  // Mostrar a seção de relatórios e ocultar as demais se necessário
  function openRelatorios() {
    if (mainContent) mainContent.style.display = 'none';
    if (usuariosSection) usuariosSection.style.display = 'none';
    if (movimentacoesSection) movimentacoesSection.style.display = 'none';
    if (configuracoesSection) configuracoesSection.style.display = 'none';
    if (relatoriosSection) relatoriosSection.style.display = 'block';
  }

  // Controla qual visualização dos relatórios está visível
  function setRelatoriosView(view) {
    if (!relatoriosSection) return;

    // Elementos originais da view de Vendas
    const chartTop = document.getElementById('chart-top-sold');
    const chartBottom = document.getElementById('chart-bottom-sold');
    const vendasTableBodyEl = document.getElementById('vendas-table-body');
    const statTicket = document.getElementById('stat-ticket-medio');

    // report-content criado dinamicamente
    const reportContainer = document.getElementById('report-content');

    // Helpers para esconder/mostrar o card que contém um elemento
    function setCardVisible(el, visible) {
      if (!el) return;
      const card = el.closest('div');
      if (card) card.style.display = visible ? '' : 'none';
    }

    if (view === 'vendas') {
      // mostrar os elementos nativos de vendas
      setCardVisible(chartTop, true);
      setCardVisible(chartBottom, true);
      if (vendasTableBodyEl) {
        const card = vendasTableBodyEl.closest('div');
        if (card) card.style.display = '';
      }
      // estatísticas
      if (statTicket) {
        const statsCard = statTicket.closest('div')?.parentElement;
        if (statsCard) statsCard.style.display = '';
      }

      // ocultar container dinâmico
      if (reportContainer) reportContainer.style.display = 'none';
    } else {
      // ocultar elementos nativos de vendas
      setCardVisible(chartTop, false);
      setCardVisible(chartBottom, false);
      if (vendasTableBodyEl) {
        const card = vendasTableBodyEl.closest('div');
        if (card) card.style.display = 'none';
      }
      if (statTicket) {
        const statsCard = statTicket.closest('div')?.parentElement;
        if (statsCard) statsCard.style.display = 'none';
      }

      // mostrar container dinâmico
      if (reportContainer) reportContainer.style.display = '';
    }
  }

  if (relVendasLink) {
    relVendasLink.addEventListener('click', (e) => {
      e.preventDefault();
      openRelatorios();
      // Carrega vendas, gráficos e estatísticas
      setRelatoriosView('vendas');
      fetchRelatorios();
    });
  }

  if (relEstoqueLink) {
    relEstoqueLink.addEventListener('click', async (e) => {
      e.preventDefault();
      openRelatorios();
      setRelatoriosView('estoque');
      const container = getReportContainer();
      container.innerHTML = '<h3>Carregando relatório de Estoque...</h3>';
      try {
        const res = await fetch('/api/estoque');
        if (!res.ok) throw new Error('Erro ao buscar estoque');
        const estoque = await parseJsonSafe(res);
        renderEstoqueReport(estoque, container);
      } catch (err) {
        console.error(err);
        container.innerHTML = '<div style="color:#ef4444">Erro ao carregar relatório de Estoque: ' + err.message + '</div>';
      }
    });
  }

  if (relValidadeLink) {
    relValidadeLink.addEventListener('click', async (e) => {
      e.preventDefault();
      openRelatorios();
      setRelatoriosView('validade');
      const container = getReportContainer();
      container.innerHTML = '<h3>Carregando relatório de Validade...</h3>';
      try {
        const res = await fetch('/api/estoque');
        if (!res.ok) throw new Error('Erro ao buscar estoque');
        const estoque = await parseJsonSafe(res);
        renderValidadeReport(estoque, container);
      } catch (err) {
        console.error(err);
        container.innerHTML = '<div style="color:#ef4444">Erro ao carregar relatório de Validade: ' + err.message + '</div>';
      }
    });
  }

  if (relFinanceiroLink) {
    relFinanceiroLink.addEventListener('click', async (e) => {
      e.preventDefault();
      openRelatorios();
      setRelatoriosView('financeiro');
      const container = getReportContainer();
      container.innerHTML = '<h3>Carregando relatório Financeiro...</h3>';
      try {
        const res = await fetch('/api/vendas');
        if (!res.ok) throw new Error('Erro ao buscar vendas');
        const vendas = await parseJsonSafe(res);
        renderFinanceiroReport(vendas, container);
      } catch (err) {
        console.error(err);
        container.innerHTML = '<div style="color:#ef4444">Erro ao carregar relatório Financeiro: ' + err.message + '</div>';
      }
    });
  }

  if (relExportLink) {
    relExportLink.addEventListener('click', (e) => {
      e.preventDefault();
      // Reutiliza função existente
      exportData();
    });
  }

  // Renderers para os novos relatórios
  function renderEstoqueReport(estoque, container) {
    if (!Array.isArray(estoque)) estoque = [];

    // Controls: filtro por nome/categoria e paginação simples
    const controlsId = 'estoque-controls';
    container.innerHTML = `
      <h3>Relatório de Estoque</h3>
      <div id="${controlsId}" style="display:flex;gap:0.5rem;margin-bottom:0.75rem;align-items:center;">
        <input id="estoque-search" type="search" placeholder="Buscar por nome ou categoria" style="flex:1;padding:0.5rem;border:1px solid #e5e7eb;border-radius:6px;" />
        <select id="estoque-filter-cat" style="padding:0.5rem;border:1px solid #e5e7eb;border-radius:6px;"><option value="">Todas as categorias</option></select>
      </div>
      <div style="margin-bottom:0.75rem;">
        <!-- botão admin será inserido aqui dinamicamente -->
        <div id="estoque-admin-actions" style="display:flex;gap:0.5rem"></div>
      </div>
      <div id="estoque-table-wrap" style="overflow-x:auto; background:white; padding:1rem; border-radius:8px; box-shadow:0 1px 2px rgba(0,0,0,0.05)"></div>
      <div id="estoque-pagination" style="display:flex;justify-content:center;gap:0.5rem;margin-top:0.75rem;"></div>
    `;

    // State for this report
    const state = { list: estoque.slice(), page: 1, perPage: 10, filter: '' };

    // Populate category filter
    const cats = Array.from(new Set(estoque.map(p => p.categoria).filter(Boolean))).sort();
    const catSelect = container.querySelector('#estoque-filter-cat');
    cats.forEach(c => { const opt = document.createElement('option'); opt.value = c; opt.textContent = c; catSelect.appendChild(opt); });

    const searchInput = container.querySelector('#estoque-search');
    searchInput.addEventListener('input', () => { state.filter = searchInput.value.trim().toLowerCase(); state.page = 1; render(); });
    catSelect.addEventListener('change', () => { state.cat = catSelect.value; state.page = 1; render(); });

    function render() {
      const tbodyRows = (state.list || []).filter(p => {
        if (state.cat && p.categoria !== state.cat) return false;
        if (!state.filter) return true;
        return (p.nome || '').toLowerCase().includes(state.filter) || (p.categoria || '').toLowerCase().includes(state.filter);
      });

      const total = tbodyRows.length;
      const totalPages = Math.max(1, Math.ceil(total / state.perPage));
      if (state.page > totalPages) state.page = totalPages;

      const start = (state.page - 1) * state.perPage;
      const pageItems = tbodyRows.slice(start, start + state.perPage);

      const isAdmin = userRole === 'admin';
      const tableHeaders = `
        <tr>
          <th style="padding:0.5rem">Código</th>
          <th style="padding:0.5rem">Nome</th>
          <th style="padding:0.5rem">Categoria</th>
          <th style="padding:0.5rem">Localização</th>
          <th style="padding:0.5rem">Quantidade</th>
          <th style="padding:0.5rem">Qtd Mínima</th>
          ${isAdmin ? '<th style="padding:0.5rem">Ações</th>' : ''}
        </tr>
      `;

      const rowsHtml = pageItems.map(p => `
        <tr>
          <td style="padding:0.5rem">${p.codigo_barras || ('PRD-' + (p.id || '').toString().padStart(3,'0'))}</td>
          <td style="padding:0.5rem">${p.nome}</td>
          <td style="padding:0.5rem">${p.categoria || ''}</td>
          <td style="padding:0.5rem">${p.localizacao || ''}</td>
          <td style="padding:0.5rem">${p.quantidade}</td>
          <td style="padding:0.5rem">${p.qtd_minima ?? ''}</td>
          ${isAdmin ? `<td style="padding:0.5rem"><button class="btn-set-limit" data-nome="${encodeURIComponent(p.nome)}">Editar Limite</button></td>` : ''}
        </tr>
      `).join('') || `<tr><td colspan="${isAdmin ? 7 : 6}" style="text-align:center;padding:1rem;color:#8A8A8A">Nenhum item no estoque.</td></tr>`;

      const tableHtml = `
        <table style="width:100%; border-collapse:collapse;">
          <thead>${tableHeaders}</thead>
          <tbody>${rowsHtml}</tbody>
        </table>
      `;

      container.querySelector('#estoque-table-wrap').innerHTML = tableHtml;

      // Attach listeners for Editar Limite buttons (admin)
      if (isAdmin) {
        container.querySelectorAll('.btn-set-limit').forEach(btn => {
          btn.addEventListener('click', async (ev) => {
            const nomeEnc = btn.getAttribute('data-nome');
            const nome = decodeURIComponent(nomeEnc);
            const novo = prompt(`Defina a quantidade mínima para "${nome}" (número):`, '0');
            if (novo === null) return;
            const novoNum = parseInt(novo, 10);
            if (isNaN(novoNum) || novoNum < 0) { alert('Quantidade mínima inválida.'); return; }
            try {
              const res = await fetch(`/api/estoque/${encodeURIComponent(nome)}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ qtd_minima: novoNum })
              });
              if (!res.ok) {
                const err = await parseJsonSafe(res).catch(e => ({ error: e.message }));
                throw new Error(err.error || 'Erro ao atualizar limite');
              }
              alert('Quantidade mínima atualizada.');
              // Recarrega dados
              await fetchAndRenderEstoque(container);
            } catch (err) {
              console.error('Erro ao atualizar limite:', err);
              alert(err.message || 'Erro ao atualizar limite');
            }
          });
        });
      }

      // pagination controls
      const pagination = container.querySelector('#estoque-pagination');
      pagination.innerHTML = '';
      const prev = document.createElement('button'); prev.textContent = 'Anterior'; prev.disabled = state.page === 1;
      const next = document.createElement('button'); next.textContent = 'Próxima'; next.disabled = state.page === totalPages;
      const info = document.createElement('span'); info.textContent = `Página ${state.page} de ${totalPages}`; info.style.alignSelf = 'center'; info.style.padding = '0 0.5rem';
      prev.addEventListener('click', () => { if (state.page > 1) { state.page--; render(); } });
      next.addEventListener('click', () => { if (state.page < totalPages) { state.page++; render(); } });
      pagination.appendChild(prev); pagination.appendChild(info); pagination.appendChild(next);
    }

    render();

      // If admin, add "Adicionar Produto" button to admin actions area
      const adminActions = container.querySelector('#estoque-admin-actions');
      if (userRole === 'admin' && adminActions) {
        adminActions.innerHTML = '';
        const addBtn = document.createElement('button');
        addBtn.textContent = '+ Adicionar Produto';
        addBtn.className = 'btn';
        addBtn.style.background = '#059669'; addBtn.style.color = 'white';
        addBtn.addEventListener('click', () => openAddProductModalForReport(container));
        adminActions.appendChild(addBtn);
      }
  }

      // Helper: refetch estoque and rerender report
      async function fetchAndRenderEstoque(container) {
        try {
          const res = await fetch('/api/estoque');
          if (!res.ok) throw new Error('Erro ao buscar estoque');
          const estoque = await parseJsonSafe(res);
          // replace state.list and re-render by calling the outer renderEstoqueReport
          renderEstoqueReport(estoque, container);
        } catch (err) {
          console.error('Erro ao recarregar estoque:', err);
          container.querySelector('#estoque-table-wrap').innerHTML = '<div style="color:#ef4444">Erro ao recarregar estoque: ' + err.message + '</div>';
        }
      }

      // Modal para adicionar produto dentro do relatório
      function openAddProductModalForReport(container) {
        const modalHtml = `
          <div id="produtoModalReport" style="position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:white;padding:20px;border-radius:8px;box-shadow:0 6px 18px rgba(0,0,0,0.15);z-index:1100;width:420px;">
            <h2>Novo Produto</h2>
            <form id="produtoFormReport">
              <div style="display:grid;gap:10px;">
                <input type="text" id="r-nome" placeholder="Nome do produto" required>
                <input type="text" id="r-codigo_barras" placeholder="Código de barras">
                <select id="r-categoria" required>
                  <option value="">Selecione a categoria</option>
                  <option value="Alimentos">Alimentos</option>
                  <option value="Bebidas">Bebidas</option>
                  <option value="Limpeza">Limpeza</option>
                  <option value="Higiene">Higiene</option>
                  <option value="Hortifruti">Hortifruti</option>
                  <option value="Padaria">Padaria</option>
                  <option value="Carnes">Carnes</option>
                  <option value="Laticínios">Laticínios</option>
                  <option value="Mercearia">Mercearia</option>
                </select>
                <input type="number" id="r-quantidade" placeholder="Quantidade" required min="0">
                <input type="number" id="r-qtd_minima" placeholder="Quantidade mínima" min="0">
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                  <input type="number" id="r-preco_custo" placeholder="Preço de custo" step="0.01" min="0">
                  <input type="number" id="r-preco_venda" placeholder="Preço de venda" step="0.01" min="0">
                </div>
                <input type="text" id="r-marca" placeholder="Marca">
                <input type="date" id="r-validade" placeholder="Data de validade">
              </div>
              <div style="display:flex;justify-content:flex-end;gap:10px;margin-top:20px;">
                <button type="button" onclick="document.getElementById('produtoModalReport')?.remove()">Cancelar</button>
                <button type="submit">Salvar</button>
              </div>
            </form>
          </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const form = document.getElementById('produtoFormReport');
        form.onsubmit = async (e) => {
          e.preventDefault();
          const produto = {
            nome: form.querySelector('#r-nome').value,
            codigo_barras: form.querySelector('#r-codigo_barras').value,
            quantidade: parseInt(form.querySelector('#r-quantidade').value, 10) || 0,
            qtd_minima: parseInt(form.querySelector('#r-qtd_minima').value, 10) || 0,
            categoria: form.querySelector('#r-categoria').value,
            preco_custo: parseFloat(form.querySelector('#r-preco_custo').value) || null,
            preco_venda: parseFloat(form.querySelector('#r-preco_venda').value) || null,
            marca: form.querySelector('#r-marca').value || '',
            validade: form.querySelector('#r-validade').value || ''
          };
          try {
            await addProduct(produto);
            document.getElementById('produtoModalReport')?.remove();
            await fetchAndRenderEstoque(container);
          } catch (err) {
            console.error('Erro ao adicionar produto pelo relatório:', err);
            alert('Erro ao adicionar produto: ' + (err.message || err));
          }
        };
      }

  function renderValidadeReport(estoque, container) {
    const hoje = new Date();
    const withValidade = (Array.isArray(estoque) ? estoque : []).filter(p => p.validade);
    const mapped = withValidade.map(p => {
      const v = new Date(p.validade);
      const dias = Math.ceil((v - hoje) / (1000*60*60*24));
      return Object.assign({}, p, { diasRestantes: dias });
    }).sort((a,b) => a.diasRestantes - b.diasRestantes);

    const rows = mapped.map(p => `
      <tr>
        <td>${p.nome}</td>
        <td>${p.validade}</td>
        <td>${p.diasRestantes}</td>
      </tr>
    `).join('');

    container.innerHTML = `
      <h3>Relatório de Validade (itens próximos da validade)</h3>
      <div style="background:white;padding:1rem;border-radius:8px;box-shadow:0 1px 2px rgba(0,0,0,0.05)">
        <table style="width:100%;border-collapse:collapse;">
          <thead><tr><th>Produto</th><th>Validade</th><th>Dias Restantes</th></tr></thead>
          <tbody>
            ${rows || '<tr><td colspan="3" style="text-align:center;padding:1rem;color:#8A8A8A">Nenhum item com validade registrada.</td></tr>'}
          </tbody>
        </table>
      </div>
    `;
  }

  function renderFinanceiroReport(vendas, container) {
    vendas = Array.isArray(vendas) ? vendas : [];

    // Novo layout Financeiro: gráfico de receita por dia + top produtos por faturamento
    container.innerHTML = `
      <h3>Relatório Financeiro</h3>
      <div style="display:grid;grid-template-columns:2fr 1fr;gap:1rem;margin-bottom:1rem;">
        <div style="background:white;padding:1rem;border-radius:8px;box-shadow:0 1px 2px rgba(0,0,0,0.05);">
          <h4 style="margin-top:0">Receita por Dia</h4>
          <canvas id="chart-fin-revenue" width="600" height="240"></canvas>
        </div>
        <div style="background:white;padding:1rem;border-radius:8px;box-shadow:0 1px 2px rgba(0,0,0,0.05);">
          <h4 style="margin-top:0">Top Produtos por Faturamento</h4>
          <canvas id="chart-fin-top" width="300" height="240"></canvas>
        </div>
      </div>
      <div id="fin-summary" style="display:flex;gap:1rem;margin-bottom:1rem;"></div>
      <div id="fin-table-wrap" style="background:white;padding:1rem;border-radius:8px;box-shadow:0 1px 2px rgba(0,0,0,0.05)"></div>
    `;

    // Preparar dados
    const parseDateKey = (d) => {
      const dt = new Date(d);
      if (isNaN(dt)) return null;
      return dt.toISOString().slice(0,10); // YYYY-MM-DD
    };

    // receita por dia
    const revenueByDay = {};
    const revenueByProduct = {};
    vendas.forEach(v => {
      const day = parseDateKey(v.data) || 'unknown';
      const valor = parseFloat(v.preco_total || 0) || 0;
      revenueByDay[day] = (revenueByDay[day] || 0) + valor;
      const prod = v.produto_nome || 'Desconhecido';
      revenueByProduct[prod] = (revenueByProduct[prod] || 0) + valor;
    });

    const daysSorted = Object.keys(revenueByDay).filter(k => k !== 'unknown').sort();
    const revenueSeries = daysSorted.map(d => revenueByDay[d]);

    // Top products
    const topProducts = Object.entries(revenueByProduct).sort((a,b) => b[1]-a[1]).slice(0,8);

    // Stats
    const totalRevenue = vendas.reduce((s,v) => s + (parseFloat(v.preco_total||0) || 0), 0);
    const totalSales = vendas.length;
    const avgTicket = totalSales ? (totalRevenue/totalSales) : 0;

    const summaryEl = container.querySelector('#fin-summary');
    summaryEl.innerHTML = `
      <div style="background:linear-gradient(135deg,#0F7490,#1A9FBE);color:white;padding:1rem;border-radius:8px;flex:1;text-align:center;">
        <div style="font-weight:700;font-size:1.25rem">R$ ${totalRevenue.toFixed(2)}</div>
        <div>Faturamento Total</div>
      </div>
      <div style="background:linear-gradient(135deg,#E8200D,#F5504D);color:white;padding:1rem;border-radius:8px;flex:1;text-align:center;">
        <div style="font-weight:700;font-size:1.25rem">${totalSales}</div>
        <div>Total de Vendas</div>
      </div>
      <div style="background:linear-gradient(135deg,#10B981,#34D399);color:white;padding:1rem;border-radius:8px;flex:1;text-align:center;">
        <div style="font-weight:700;font-size:1.25rem">R$ ${avgTicket.toFixed(2)}</div>
        <div>Ticket Médio</div>
      </div>
    `;

    // Render table (últimas 50 vendas)
    const tableWrap = container.querySelector('#fin-table-wrap');
    tableWrap.innerHTML = `
      <h4>Últimas Vendas</h4>
      <table style="width:100%;border-collapse:collapse;">
        <thead><tr><th style="padding:0.5rem">Data</th><th style="padding:0.5rem">Produto</th><th style="padding:0.5rem">Qtd</th><th style="padding:0.5rem">Total</th></tr></thead>
        <tbody>
          ${vendas.slice(0,50).map(v => `<tr><td style="padding:0.5rem">${new Date(v.data).toLocaleString('pt-BR')}</td><td style="padding:0.5rem">${v.produto_nome}</td><td style="padding:0.5rem">${v.quantidade}</td><td style="padding:0.5rem">R$ ${parseFloat(v.preco_total||0).toFixed(2)}</td></tr>`).join('') || '<tr><td colspan="4" style="text-align:center;padding:1rem;color:#8A8A8A">Nenhuma venda registrada.</td></tr>'}
        </tbody>
      </table>
    `;

    // Charts (Chart.js já carregado)
    try {
      const ctxRev = document.getElementById('chart-fin-revenue');
      if (ctxRev) {
        if (charts.finRevenue) charts.finRevenue.destroy();
        charts.finRevenue = new Chart(ctxRev, {
          type: 'line',
          data: { labels: daysSorted, datasets: [{ label: 'Receita (R$)', data: revenueSeries, borderColor: '#0F7490', backgroundColor: 'rgba(15,116,144,0.08)', fill: true, tension: 0.3 }] },
          options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { ticks: { color: '#595959' } }, y: { ticks: { color: '#595959' } } } }
        });
      }

      const ctxTop = document.getElementById('chart-fin-top');
      if (ctxTop) {
        if (charts.finTop) charts.finTop.destroy();
        charts.finTop = new Chart(ctxTop, {
          type: 'bar',
          data: { labels: topProducts.map(t => t[0]), datasets: [{ label: 'Faturamento (R$)', data: topProducts.map(t => t[1]), backgroundColor: '#E8200D' }] },
          options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { ticks: { color: '#595959' } }, y: { ticks: { color: '#595959' } } } }
        });
      }
    } catch (err) {
      console.error('Erro ao gerar gráficos financeiros:', err);
    }
  }

  // Fetch products from backend API
  async function fetchProducts() {
    try {
      const response = await fetch('/api/estoque');
      if (!response.ok) throw new Error('Erro ao buscar produtos');
      products = await parseJsonSafe(response);
      filteredProducts = products;
      currentPage = 1;
      renderTable();
      updatePagination();
    } catch (error) {
      console.error('Erro ao carregar produtos:', error);
      alert(error.message);
    }
  }

  // Helper: safely parse JSON responses, fallback to text for diagnostics
  async function parseJsonSafe(response) {
    const text = await response.text();
    const ct = response.headers.get('content-type') || '';
    if (ct.includes('application/json')) {
      try {
        return JSON.parse(text);
      } catch (e) {
        throw new Error('Resposta JSON inválida: ' + e.message + '\n' + text);
      }
    }
    // not JSON -> include body so user sees the HTML or error
    throw new Error(text || 'Resposta inesperada do servidor');
  }

  // Render products table
  function renderTable() {
    productTableBody.innerHTML = '';
    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const pageItems = filteredProducts.slice(start, end);

    if (pageItems.length === 0) {
      productTableBody.innerHTML = '<tr><td colspan="7" style="text-align:center;">Nenhum produto encontrado.</td></tr>';
      return;
    }

    pageItems.forEach(product => {
      const tr = document.createElement('tr');

      const codeTd = document.createElement('td');
      codeTd.textContent = product.codigo_barras || `PRD-${product.id.toString().padStart(3, '0')}`;
      tr.appendChild(codeTd);

      const nameTd = document.createElement('td');
      nameTd.textContent = product.nome;
      if (product.marca) {
        nameTd.innerHTML += `<br><small style="color:#6b7280">${product.marca}</small>`;
      }
      tr.appendChild(nameTd);

      const categoryTd = document.createElement('td');
      categoryTd.textContent = product.categoria || '';
      tr.appendChild(categoryTd);

      const precoTd = document.createElement('td');
      if (product.preco_venda != null && typeof product.preco_venda === 'number') {
        precoTd.innerHTML = `R$ ${product.preco_venda.toFixed(2)}`;
        if (product.preco_custo != null && typeof product.preco_custo === 'number') {
          const margem = ((product.preco_venda - product.preco_custo) / product.preco_custo * 100).toFixed(1);
          precoTd.innerHTML += `<br><small style="color:#059669">+${margem}%</small>`;
        }
      } else {
        precoTd.textContent = '-';
      }
      tr.appendChild(precoTd);

      const qtdTd = document.createElement('td');
      const qtdText = `${product.quantidade} ${product.unidade_medida || 'un'}`;
      qtdTd.innerHTML = product.quantidade < (product.qtd_minima || 0)
        ? `${qtdText}<br><small style="color:#ef4444">Abaixo do mínimo</small>`
        : qtdText;
      tr.appendChild(qtdTd);

      const validadeTd = document.createElement('td');
      if (product.validade) {
        const validade = new Date(product.validade);
        const hoje = new Date();
        const diasRestantes = Math.ceil((validade - hoje) / (1000 * 60 * 60 * 24));
        const cor = diasRestantes <= 7 ? '#ef4444' : diasRestantes <= 30 ? '#f59e0b' : '#10b981';
        validadeTd.innerHTML = `${validade.toLocaleDateString('pt-BR')}<br><small style="color:${cor}">${diasRestantes} dias</small>`;
      }
      tr.appendChild(validadeTd);

      const actionsTd = document.createElement('td');
      actionsTd.classList.add('actions');

      // Botão Editar
      const editBtn = document.createElement('button');
      editBtn.classList.add('btn-edit');
      editBtn.textContent = 'Editar';
      editBtn.addEventListener('click', async () => {
        // Abre prompts para editar os campos principais
        const novoNome = prompt('Editar nome do produto:', product.nome);
        if (!novoNome) return;
        const novaQtd = parseInt(prompt('Editar quantidade:', product.quantidade), 10);
        if (isNaN(novaQtd)) return;
        const novaQtdMin = parseInt(prompt('Editar quantidade mínima:', product.qtd_minima), 10);
        const novaCategoria = prompt('Editar categoria:', product.categoria || '');
        const novoFornecedor = prompt('Editar fornecedor:', product.fornecedor || '');
        const novaLocalizacao = prompt('Editar localização:', product.localizacao || '');
        // Envia PUT para backend
        try {
          const res = await fetch(`/api/estoque/${encodeURIComponent(product.nome)}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              nome: novoNome,
              quantidade: novaQtd,
              qtd_minima: novaQtdMin,
              categoria: novaCategoria,
              fornecedor: novoFornecedor,
              localizacao: novaLocalizacao
            })
          });
          if (!res.ok) throw new Error('Erro ao editar produto');
          alert('Produto editado com sucesso!');
          fetchProducts();
        } catch (err) {
          console.error('Erro ao editar produto:', err);
          alert(err.message);
        }
      });
      actionsTd.appendChild(editBtn);

      // Botão Movimentar
      const moveBtn = document.createElement('button');
      moveBtn.classList.add('btn-move');
      moveBtn.textContent = 'Movimentar';
      moveBtn.addEventListener('click', () => {
        openMovimentacao(product, 'Saída');
      });
      actionsTd.appendChild(moveBtn);

      // Botão Deletar
      const delBtn = document.createElement('button');
      delBtn.classList.add('btn-delete');
      delBtn.textContent = 'Deletar';
      delBtn.style.backgroundColor = '#ef4444';
      delBtn.style.color = 'white';
      delBtn.addEventListener('click', async () => {
        if (!confirm(`Tem certeza que deseja deletar o produto "${product.nome}"?`)) return;
        try {
          const res = await fetch(`/api/estoque/${encodeURIComponent(product.nome)}`, {
            method: 'DELETE'
          });
          if (!res.ok) throw new Error('Erro ao deletar produto');
          alert('Produto deletado com sucesso!');
          fetchProducts();
        } catch (err) {
          console.error('Erro ao deletar produto:', err);
          alert(err.message);
        }
      });
      actionsTd.appendChild(delBtn);

      tr.appendChild(actionsTd);
      productTableBody.appendChild(tr);
    });
  }

  // Update pagination controls
  function updatePagination() {
    const totalPages = Math.ceil(filteredProducts.length / itemsPerPage);
    currentPageSpan.textContent = `Página ${currentPage} de ${totalPages}`;
    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = currentPage === totalPages || totalPages === 0;
  }

  // Pagination button handlers
  if (prevBtn) {
    prevBtn.addEventListener('click', () => {
      if (currentPage > 1) {
        currentPage--;
        renderTable();
        updatePagination();
      }
    });
  }
  if (nextBtn) {
    nextBtn.addEventListener('click', () => {
      const totalPages = Math.ceil(filteredProducts.length / itemsPerPage);
      if (currentPage < totalPages) {
        currentPage++;
        renderTable();
        updatePagination();
      }
    });
  }

  // Filter products based on search input
  if (searchInput) {
    searchInput.addEventListener('input', () => {
    const searchTerm = searchInput.value.toLowerCase();
    filteredProducts = products.filter(p =>
      p.nome.toLowerCase().includes(searchTerm) ||
      (p.categoria && p.categoria.toLowerCase().includes(searchTerm))
    );
    currentPage = 1;
    renderTable();
    updatePagination();
    });
  }

  // Fetch users from backend API
  async function fetchUsers() {
    try {
      const response = await fetch('/api/users');
      if (!response.ok) throw new Error('Erro ao buscar usuários');
      const users = await parseJsonSafe(response);
      renderUsersTable(users);
    } catch (error) {
      console.error('Erro ao carregar usuários:', error);
      alert(error.message);
    }
  }

  // Render users table
  function renderUsersTable(users) {
    usersTableBody.innerHTML = '';
    if (users.length === 0) {
      usersTableBody.innerHTML = '<tr><td colspan="3" style="text-align:center;">Nenhum usuário encontrado.</td></tr>';
      return;
    }
    users.forEach(user => {
      const tr = document.createElement('tr');

      const usernameTd = document.createElement('td');
      usernameTd.textContent = user.username;
      tr.appendChild(usernameTd);

      const roleTd = document.createElement('td');
      roleTd.textContent = user.role;
      tr.appendChild(roleTd);

      const actionsTd = document.createElement('td');
      actionsTd.classList.add('actions');

      const editBtn = document.createElement('button');
      editBtn.classList.add('btn-edit');
      editBtn.textContent = 'Editar';
      editBtn.addEventListener('click', async () => {
        const novoNome = prompt('Novo nome de usuário:', user.username);
        const novaSenha = prompt('Nova senha (deixe em branco para manter):', '');
        const novaRole = prompt('Função (admin/user):', user.role || 'user');
        try {
          const res = await fetch(`/api/users/${encodeURIComponent(user.username)}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: novoNome, password: novaSenha || undefined, role: novaRole })
          });
          if (!res.ok) {
            const err = await parseJsonSafe(res).catch(e => ({ error: e.message }));
            throw new Error(err.error || 'Erro ao editar usuário');
          }
          alert('Usuário atualizado com sucesso');
          fetchUsers();
        } catch (err) {
          console.error('Erro ao editar usuário:', err);
          alert(err.message);
        }
      });
      actionsTd.appendChild(editBtn);

      // Botão Deletar
      const delBtn = document.createElement('button');
      delBtn.classList.add('btn-delete');
      delBtn.textContent = 'Deletar';
      delBtn.style.backgroundColor = '#ef4444';
      delBtn.style.color = 'white';
      delBtn.addEventListener('click', async () => {
        if (!confirm(`Confirma remoção do usuário ${user.username}?`)) return;
        try {
          const res = await fetch(`/api/users/${encodeURIComponent(user.username)}`, { method: 'DELETE' });
          if (!res.ok) {
            const err = await parseJsonSafe(res).catch(e => ({ error: e.message }));
            throw new Error(err.error || 'Erro ao deletar usuário');
          }
          alert('Usuário deletado com sucesso');
          fetchUsers();
        } catch (err) {
          console.error('Erro ao deletar usuário:', err);
          alert(err.message);
        }
      });
      actionsTd.appendChild(delBtn);

      tr.appendChild(actionsTd);

      usersTableBody.appendChild(tr);
    });
  }

  // Add new user event
  if (addUserBtn) {
    addUserBtn.addEventListener('click', () => {
    const username = prompt('Digite o nome do usuário:');
    const password = prompt('Digite a senha:');
    const role = prompt('Digite a função (ex: admin, user):');
    if (username && password && role) {
      addUser({ username, password, role });
    } else {
      alert('Todos os campos são obrigatórios.');
    }
    });
  }

  // Add user via API
  async function addUser(user) {
    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(user)
      });
      if (!response.ok) {
        const errorData = await parseJsonSafe(response);
        throw new Error(errorData.error || 'Erro ao adicionar usuário');
      }
      alert('Usuário adicionado com sucesso!');
      fetchUsers();
    } catch (error) {
      console.error('Erro ao adicionar usuário:', error);
      alert(error.message);
    }
  }

  // Fetch movimentacoes from backend API
  async function fetchMovimentacoes() {
    try {
      const response = await fetch('/api/relatorio');
      if (!response.ok) throw new Error('Erro ao buscar movimentações');
      const movimentacoes = await parseJsonSafe(response);
      renderMovimentacoesTable(movimentacoes);
    } catch (error) {
      console.error('Erro ao carregar movimentações:', error);
      alert(error.message);
    }
  }

  // Render movimentacoes table
  function renderMovimentacoesTable(movimentacoes) {
    movimentacoesTableBody.innerHTML = '';
    if (movimentacoes.length === 0) {
      movimentacoesTableBody.innerHTML = '<tr><td colspan="5" style="text-align:center;">Nenhuma movimentação encontrada.</td></tr>';
      return;
    }
    movimentacoes.forEach(mov => {
      const tr = document.createElement('tr');

      const produtoTd = document.createElement('td');
      produtoTd.textContent = mov.nome;
      tr.appendChild(produtoTd);

      const qtdTd = document.createElement('td');
      qtdTd.textContent = mov.quantidade;
      tr.appendChild(qtdTd);

      const respTd = document.createElement('td');
      respTd.textContent = mov.responsavel;
      tr.appendChild(respTd);

      const motivoTd = document.createElement('td');
      motivoTd.textContent = mov.motivo;
      tr.appendChild(motivoTd);

      const dataTd = document.createElement('td');
      dataTd.textContent = new Date(mov.data).toLocaleString('pt-BR');
      tr.appendChild(dataTd);

      movimentacoesTableBody.appendChild(tr);
    });
  }

  // Export data to CSV
  function exportData() {
    if (products.length === 0) {
      alert('Nenhum produto para exportar.');
      return;
    }
    const csv = [
      ['Código', 'Nome', 'Categoria', 'Localização', 'Quantidade', 'Qtd Mínima'],
      ...products.map(p => [
        p.codigo || `PRD-${p.id.toString().padStart(3, '0')}`,
        p.nome,
        p.categoria || '',
        p.localizacao || '',
        p.quantidade,
        p.qtd_minima || ''
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'estoque.csv';
    a.click();
    URL.revokeObjectURL(url);
  }

  // Add product event: Opens a modal form to collect product details and submits to API
  if (addProductBtn) {
    addProductBtn.addEventListener('click', () => {
      // Create modal for new product input
      const modalHtml = `
        <div id="produtoModal" style="position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:white;padding:20px;border-radius:8px;box-shadow:0 4px 6px rgba(0,0,0,0.1);z-index:1000;width:400px;">
          <h2>Novo Produto</h2>
          <form id="produtoForm">
            <div style="display:grid;gap:10px;">
              <input type="text" id="nome" placeholder="Nome do produto" required>
              <input type="text" id="codigo_barras" placeholder="Código de barras">
              <select id="categoria" required>
                <option value="">Selecione a categoria</option>
                <option value="Alimentos">Alimentos</option>
                <option value="Bebidas">Bebidas</option>
                <option value="Limpeza">Limpeza</option>
                <option value="Higiene">Higiene</option>
                <option value="Hortifruti">Hortifruti</option>
                <option value="Padaria">Padaria</option>
                <option value="Carnes">Carnes</option>
                <option value="Laticínios">Laticínios</option>
                <option value="Mercearia">Mercearia</option>
              </select>
              <input type="number" id="quantidade" placeholder="Quantidade" required min="0">
              <input type="number" id="qtd_minima" placeholder="Quantidade mínima" min="0">
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                <input type="number" id="preco_custo" placeholder="Preço de custo" step="0.01" min="0">
                <input type="number" id="preco_venda" placeholder="Preço de venda" step="0.01" min="0">
              </div>
              <input type="text" id="marca" placeholder="Marca">
              <input type="text" id="unidade_medida" placeholder="Unidade (kg, l, un)">
              <input type="text" id="peso_volume" placeholder="Peso/Volume">
              <input type="text" id="fornecedor" placeholder="Fornecedor">
              <input type="date" id="validade" placeholder="Data de validade">
            </div>
            <div style="display:flex;justify-content:flex-end;gap:10px;margin-top:20px;">
              <button type="button" onclick="document.getElementById('produtoModal').remove()">Cancelar</button>
              <button type="submit">Salvar</button>
            </div>
          </form>
        </div>
      `;
      document.body.insertAdjacentHTML('beforeend', modalHtml);

      const form = document.getElementById('produtoForm');
      form.onsubmit = async (e) => {
        e.preventDefault();
        const produto = {
          nome: form.nome.value,
          codigo_barras: form.codigo_barras.value,
          quantidade: parseInt(form.quantidade.value),
          qtd_minima: parseInt(form.qtd_minima.value) || 0,
          categoria: form.categoria.value,
          preco_custo: parseFloat(form.preco_custo.value) || null,
          preco_venda: parseFloat(form.preco_venda.value) || null,
          marca: form.marca.value,
          unidade_medida: form.unidade_medida.value,
          peso_volume: form.peso_volume.value,
          fornecedor: form.fornecedor.value,
          validade: form.validade.value,
          localizacao: '' // Default location if not provided
        };

        // Basic validation
        if (!produto.nome || isNaN(produto.quantidade) || produto.quantidade < 0) {
          alert('Nome e quantidade válida são obrigatórios.');
          return;
        }

        try {
          await addProduct(produto);
          document.getElementById('produtoModal').remove();
        } catch (err) {
          console.error('Erro ao adicionar produto:', err);
          alert('Erro ao adicionar produto: ' + err.message);
        }
      };
    });
  }

  // Add product via API
  async function addProduct(product) {
    try {
      const response = await fetch('/api/estoque', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(product)
      });
      if (!response.ok) {
        const errorData = await parseJsonSafe(response);
        throw new Error(errorData.error || 'Erro ao adicionar produto');
      }
      alert('Produto adicionado com sucesso!');
      fetchProducts();
    } catch (error) {
      console.error('Erro ao adicionar produto:', error);
      alert(error.message);
    }
  }

  // Export button
  if (exportBtn) exportBtn.addEventListener('click', exportData);

  // Quick actions in sidebar: Handle simple prompts for stock entry/exit
  if (quickActionBtns) {
    quickActionBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const action = btn.textContent.trim();
        if (action === 'Entrada de Estoque') {
          const nome = prompt('Nome do produto:');
          const quantidade = parseInt(prompt('Quantidade a adicionar:'), 10);
          const categoria = prompt('Categoria (opcional):') || null;
          const fornecedor = prompt('Fornecedor (opcional):') || null;
          const localizacao = prompt('Localização (opcional):') || null;
          if (nome && !isNaN(quantidade) && quantidade > 0) {
            addProduct({ nome, quantidade, categoria, fornecedor, localizacao });
          } else {
            alert('Nome e quantidade válida são obrigatórios.');
          }
        } else if (action === 'Saída de Estoque') {
          const nome = prompt('Nome do produto:');
          const quantidade = parseInt(prompt('Quantidade a retirar:'), 10);
          const responsavel = prompt('Responsável pela saída:');
          const motivo = prompt('Motivo da saída:');
          if (nome && !isNaN(quantidade) && quantidade > 0 && responsavel && motivo) {
            retirada({ nome, quantidade, responsavel, motivo });
          } else {
            alert('Todos os campos são obrigatórios para saída.');
          }
        }
      });
    });
  }

  // Auto-replenish low stock items via quick action link
  if (quickActionLink) {
    quickActionLink.addEventListener('click', async () => {
      const lowItems = products.filter(p => p.quantidade < (p.qtd_minima || 0));
      if (lowItems.length === 0) {
        alert('Nenhum item abaixo do mínimo.');
        return;
      }
      if (!confirm(`Repor ${lowItems.length} itens abaixo do mínimo?`)) return;

      try {
        for (const item of lowItems) {
          const addQtd = (item.qtd_minima || 0) - item.quantidade;
          if (addQtd > 0) {
            await addProduct({ nome: item.nome, quantidade: addQtd });
          }
        }
        alert('Itens repostos com sucesso!');
        fetchProducts(); // Refresh data
      } catch (err) {
        console.error('Erro ao repor itens:', err);
        alert('Erro ao repor itens: ' + err.message);
      }
    });
  }

  // Perform stock withdrawal: Updates stock and logs to relatorio
  async function retirada(data) {
    try {
      const response = await fetch('/api/retirada', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) {
        const errorData = await parseJsonSafe(response);
      }
      alert('Retirada registrada com sucesso!');
      await fetchProducts(); // Refresh products
      if (movimentacoesSection) { // If in movements section, refresh table
        await fetchMovimentacoes();
      }
    } catch (error) {
      console.error('Erro na retirada:', error);
      alert(error.message);
    }
  }

  // Abrir formulário de movimentação para um produto (tipo: 'Entrada' ou 'Saída')
  function openMovimentacao(product, tipo = 'Saída') {
    // Navega para a aba de Movimentações
    const movLink = Array.from(navLinks).find(l => l.textContent.trim() === 'Movimentações');
    if (movLink) {
      movLink.click();
    } else {
      // fallback: mostra a seção diretamente
      if (mainContent) mainContent.style.display = 'none';
      if (usuariosSection) usuariosSection.style.display = 'none';
      if (movimentacoesSection) movimentacoesSection.style.display = 'block';
      if (configuracoesSection) configuracoesSection.style.display = 'none';
    }

    if (!movimentacaoForm) return;
    if (movProduto) movProduto.value = product.nome || '';
    if (movTipo) movTipo.value = tipo;
    if (movQuantidade) movQuantidade.value = '';
    if (movLocal) movLocal.value = product.localizacao || '';
    if (movObservacoes) movObservacoes.value = '';

    // Atualiza resumo
    if (resumoQtdAtual) resumoQtdAtual.textContent = product.quantidade ?? 0;
    if (resumoQtdMinima) resumoQtdMinima.textContent = product.qtd_minima ?? 0;
    if (resumoLocal) resumoLocal.textContent = product.localizacao || '-';
    if (resumoCategoria) resumoCategoria.textContent = product.categoria || '-';
  }

  function clearMovimentacaoForm() {
    if (!movimentacaoForm) return;
    if (movProduto) movProduto.value = '';
    if (movTipo) movTipo.value = '';
    if (movQuantidade) movQuantidade.value = '';
    if (movLocal) movLocal.value = '';
    if (movObservacoes) movObservacoes.value = '';
    if (resumoQtdAtual) resumoQtdAtual.textContent = '0';
    if (resumoQtdMinima) resumoQtdMinima.textContent = '0';
    if (resumoLocal) resumoLocal.textContent = '-';
    if (resumoCategoria) resumoCategoria.textContent = '-';
  }

  if (movimentacaoForm) {
    movimentacaoForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const nome = movProduto ? movProduto.value : null;
      const quantidade = movQuantidade ? parseInt(movQuantidade.value, 10) : null;
      const tipo = movTipo ? movTipo.value : 'Saída';
      const local = movLocal ? movLocal.value : '';
      const motivo = movObservacoes ? movObservacoes.value : '';

      if (!nome || !quantidade || quantidade <= 0) {
        alert('Produto e quantidade válidos são obrigatórios.');
        return;
      }

      try {
        if (tipo === 'Entrada') {
          await addProduct({ nome, quantidade, localizacao: local });
          alert('Entrada registrada com sucesso!');
        } else {
          await retirada({ nome, quantidade, responsavel: 'web', motivo, usuario_id: userData.id });
          alert('Saída registrada com sucesso!');
        }
        clearMovimentacaoForm();
        fetchProducts();
        fetchMovimentacoes();
      } catch (err) {
        console.error('Erro ao processar movimentação:', err);
        alert(err.message || 'Erro ao processar movimentação');
      }
    });
  }

  // ===== FUNÇÕES DE RELATÓRIOS =====
  async function fetchRelatorios() {
    try {
      // Buscar vendas do banco
      const response = await fetch('/api/vendas');
      if (!response.ok) throw new Error('Erro ao buscar vendas');
      const vendas = await parseJsonSafe(response);
      
      // Renderizar tabela de vendas
      renderVendasTable(vendas);
      
      // Buscar estatísticas
      const topResponse = await fetch('/api/vendas/stats/top');
      const topData = await parseJsonSafe(topResponse);
      
      const bottomResponse = await fetch('/api/vendas/stats/bottom');
      const bottomData = await parseJsonSafe(bottomResponse);
      
      // Renderizar gráficos
      renderCharts(topData, bottomData, vendas);
      
      // Calcular e exibir estatísticas
      calcularEstatisticas(vendas);
    } catch (error) {
      console.error('Erro ao carregar relatórios:', error);
      alert('Erro ao carregar relatórios: ' + error.message);
    }
  }

  function renderVendasTable(vendas) {
    if (!vendasTableBody) return;
    
    vendasTableBody.innerHTML = '';
    if (vendas.length === 0) {
      vendasTableBody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 2rem; color: #8A8A8A;">Nenhuma venda registrada.</td></tr>';
      return;
    }

    // Criar mapa de usuários para não fazer múltiplas requisições
    const usuariosMap = {};
    
    vendas.slice(0, 20).forEach(async (venda) => {
      const tr = document.createElement('tr');
      tr.style.borderBottom = '1px solid #EBEBEB';

      const produtoTd = document.createElement('td');
      produtoTd.textContent = venda.produto_nome;
      produtoTd.style.padding = '0.75rem';
      tr.appendChild(produtoTd);

      const qtdTd = document.createElement('td');
      qtdTd.textContent = venda.quantidade;
      qtdTd.style.padding = '0.75rem';
      tr.appendChild(qtdTd);

      const precoUnitTd = document.createElement('td');
      precoUnitTd.textContent = `R$ ${parseFloat(venda.preco_unitario || 0).toFixed(2)}`;
      precoUnitTd.style.padding = '0.75rem';
      tr.appendChild(precoUnitTd);

      const totalTd = document.createElement('td');
      totalTd.textContent = `R$ ${parseFloat(venda.preco_total || 0).toFixed(2)}`;
      totalTd.style.padding = '0.75rem';
      totalTd.style.fontWeight = '600';
      totalTd.style.color = '#E8200D';
      tr.appendChild(totalTd);

      const vendedorTd = document.createElement('td');
      let vendedorNome = 'Sistema';
      if (venda.usuario_id) {
        if (usuariosMap[venda.usuario_id]) {
          vendedorNome = usuariosMap[venda.usuario_id];
        } else {
          try {
            const userRes = await fetch(`/api/users/${venda.usuario_id}`);
            if (userRes.ok) {
              const userData = await userRes.json();
              usuariosMap[venda.usuario_id] = userData.username;
              vendedorNome = userData.username;
            }
          } catch (err) {
            console.error('Erro ao buscar usuário:', err);
          }
        }
      }
      vendedorTd.textContent = vendedorNome;
      vendedorTd.style.padding = '0.75rem';
      tr.appendChild(vendedorTd);

      const dataTd = document.createElement('td');
      dataTd.textContent = new Date(venda.data).toLocaleString('pt-BR');
      dataTd.style.padding = '0.75rem';
      tr.appendChild(dataTd);

      vendasTableBody.appendChild(tr);
    });
  }

  function renderCharts(topData, bottomData, vendas) {
    // Gráfico de Produtos Mais Vendidos
    const ctxTop = document.getElementById('chart-top-sold');
    if (ctxTop && topData.length > 0) {
      if (charts.topSold) charts.topSold.destroy();
      
      charts.topSold = new Chart(ctxTop, {
        type: 'bar',
        data: {
          labels: topData.map(d => d.produto_nome),
          datasets: [{
            label: 'Quantidade Vendida',
            data: topData.map(d => d.total_vendas),
            backgroundColor: '#E8200D',
            borderColor: '#C91809',
            borderWidth: 1,
            borderRadius: 4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          plugins: {
            legend: { display: true, position: 'top' }
          },
          scales: {
            y: { beginAtZero: true, ticks: { color: '#595959' } },
            x: { ticks: { color: '#595959' } }
          }
        }
      });
    }

    // Gráfico de Produtos Menos Vendidos
    const ctxBottom = document.getElementById('chart-bottom-sold');
    if (ctxBottom && bottomData.length > 0) {
      if (charts.bottomSold) charts.bottomSold.destroy();
      
      charts.bottomSold = new Chart(ctxBottom, {
        type: 'doughnut',
        data: {
          labels: bottomData.slice(0, 5).map(d => d.produto_nome),
          datasets: [{
            data: bottomData.slice(0, 5).map(d => d.total_vendas || 0),
            backgroundColor: ['#0F7490', '#1A9FBE', '#10B981', '#F59E0B', '#8B5CF6'],
            borderColor: '#FFFFFF',
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          plugins: {
            legend: { display: true, position: 'bottom' }
          }
        }
      });
    }
  }

  function calcularEstatisticas(vendas) {
    if (vendas.length === 0) return;

    // Total de vendas
    const totalVendas = vendas.length;
    document.querySelector('[style*="Total de Vendas"]').parentElement.textContent = totalVendas;

    // Faturamento total
    const faturamentoTotal = vendas.reduce((sum, v) => sum + parseFloat(v.preco_total || 0), 0);
    document.querySelector('[style*="Faturamento Total"]').parentElement.textContent = `R$ ${faturamentoTotal.toFixed(2)}`;

    // Ticket médio
    const ticketMedio = faturamentoTotal / totalVendas;
    const ticketElement = document.getElementById('stat-ticket-medio');
    if (ticketElement) ticketElement.textContent = `R$ ${ticketMedio.toFixed(2)}`;

    // Margem média (simplificado)
    const marginElement = document.getElementById('stat-margin');
    if (marginElement) marginElement.textContent = '0%'; // Será calculado com mais dados
  }
});
