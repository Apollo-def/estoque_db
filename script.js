// SPA Navigation and API Integration for Almoxarifado

document.addEventListener('DOMContentLoaded', () => {
  // Check if user is logged in
  const user = localStorage.getItem('user');
  if (!user) {
    window.location.href = 'login.html';
    return;
  }

  // Cache DOM elements
  const navLinks = document.querySelectorAll('.nav-links a');
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
  const addProductBtn = document.querySelector('.header-buttons .btn:first-child');
  const exportBtn = document.querySelector('.header-buttons .btn:last-child');
  const quickActionBtns = document.querySelectorAll('.sidebar-right .quick-action-btn');
  const quickActionLink = document.querySelector('.sidebar-right .quick-action-link');

  let currentPage = 1;
  const itemsPerPage = 10;
  let products = [];
  let filteredProducts = [];

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
      codeTd.textContent = product.codigo || `PRD-${product.id.toString().padStart(3, '0')}`;
      tr.appendChild(codeTd);

      const nameTd = document.createElement('td');
      nameTd.textContent = product.nome;
      tr.appendChild(nameTd);

      const categoryTd = document.createElement('td');
      categoryTd.textContent = product.categoria || '';
      tr.appendChild(categoryTd);

      const localTd = document.createElement('td');
      localTd.textContent = product.localizacao || '';
      tr.appendChild(localTd);

      const qtdAtualTd = document.createElement('td');
      qtdAtualTd.innerHTML = product.quantidade < (product.qtd_minima || 0)
        ? `${product.quantidade}<br /><small style="color:#6366f1;">Abaixo do mínimo</small>`
        : product.quantidade;
      tr.appendChild(qtdAtualTd);

      const qtdMinTd = document.createElement('td');
      qtdMinTd.textContent = product.qtd_minima || '';
      tr.appendChild(qtdMinTd);

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

  // Add product event
  if (addProductBtn) {
    addProductBtn.addEventListener('click', () => {
    const nome = prompt('Nome do produto:');
    const quantidade = parseInt(prompt('Quantidade:'));
    const qtd_minima = parseInt(prompt('Quantidade mínima:'));
    const categoria = prompt('Categoria:');
    const fornecedor = prompt('Fornecedor:');
    const localizacao = prompt('Localização:');
    if (nome && !isNaN(quantidade)) {
      addProduct({ nome, quantidade, qtd_minima, categoria, fornecedor, localizacao });
    } else {
      alert('Nome e quantidade são obrigatórios.');
    }
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
      alert(error.message);
    }
  }

  // Export button
  if (exportBtn) exportBtn.addEventListener('click', exportData);

  // Quick actions
  if (quickActionBtns) {
    quickActionBtns.forEach(btn => {
      btn.addEventListener('click', () => {
      const action = btn.textContent.trim();
      if (action === 'Entrada de Estoque') {
        const nome = prompt('Nome do produto:');
        const quantidade = parseInt(prompt('Quantidade a adicionar:'));
        const categoria = prompt('Categoria:');
        const fornecedor = prompt('Fornecedor:');
        const localizacao = prompt('Localização:');
        if (nome && !isNaN(quantidade)) {
          addProduct({ nome, quantidade, categoria, fornecedor, localizacao });
        }
      } else if (action === 'Saída de Estoque') {
        const nome = prompt('Nome do produto:');
        const quantidade = parseInt(prompt('Quantidade a retirar:'));
        const responsavel = prompt('Responsável:');
        const motivo = prompt('Motivo:');
        if (nome && !isNaN(quantidade) && responsavel && motivo) {
          retirada({ nome, quantidade, responsavel, motivo });
        }
      }
      });
    });
  }

  // Repor itens
  if (quickActionLink) quickActionLink.addEventListener('click', () => {
    const lowItems = products.filter(p => p.quantidade < (p.qtd_minima || 0));
    if (lowItems.length === 0) {
      alert('Nenhum item abaixo do mínimo.');
      return;
    }
    lowItems.forEach(item => {
      const addQtd = (item.qtd_minima || 0) - item.quantidade;
      if (addQtd > 0) {
        addProduct({ nome: item.nome, quantidade: addQtd });
      }
    });
  });

  // Retirada via API
  async function retirada(data) {
    try {
      const response = await fetch('/api/retirada', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) {
        const errorData = await parseJsonSafe(response);
        throw new Error(errorData.error || 'Erro na retirada');
      }
      alert('Retirada registrada com sucesso!');
      fetchProducts();
    } catch (error) {
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
          await retirada({ nome, quantidade, responsavel: 'web', motivo });
          alert('Saída registrada com sucesso!');
        }
        clearMovimentacaoForm();
        fetchProducts();
        fetchMovimentacoes();
      } catch (err) {
        alert(err.message || 'Erro ao processar movimentação');
      }
    });
  }
});
