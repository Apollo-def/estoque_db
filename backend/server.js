/**
 * Sistema de Gerenciamento para Mercearia
 * 
 * Este arquivo implementa o servidor backend usando Express.js, fornecendo APIs para:
 * - Gerenciamento de produtos e estoque
 * - Controle de vendas e preços
 * - Autenticação de usuários e controle de acesso
 * - Relatórios financeiros e de estoque
 * - Gestão de validade de produtos
 * 
 * Banco de dados: MySQL
 * Autenticação: JWT + bcrypt
 * CORS: Habilitado para desenvolvimento local
 */

// Importações principais
const express = require('express');     // Framework web
const mysql = require('mysql2/promise'); // Driver MySQL com suporte a async/await
const bodyParser = require('body-parser'); // Parser para requisições JSON
const cors = require('cors');            // Middleware CORS para desenvolvimento

const path = require('path'); // Módulo para manipulação de caminhos de arquivos
// Carrega variáveis de ambiente de um arquivo .env se existir
try {
  require('dotenv').config();
} catch (e) {
  // dotenv não está instalado — continuar sem .env
}

// bcrypt pode ser opcional no ambiente local; preferir bcryptjs se bcrypt não estiver disponível
let bcrypt;
try {
  bcrypt = require('bcrypt');
} catch (e) {
  try {
    bcrypt = require('bcryptjs');
  } catch (e2) {
    bcrypt = null;
  }
}
const app = express(); // Instância da aplicação Express
const port = process.env.PORT || 3000; // Porta em que o servidor irá rodar

// Configuração de middlewares
app.use(cors()); // Habilita CORS para permitir requisições de origens diferentes (ex: frontend)
app.use(bodyParser.json()); // Parseia o corpo das requisições como JSON

// Logger simples de requisições
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} ${req.method} ${req.url}`);
  next();
});

// Rotas para servir arquivos HTML principais (serão servidos mais abaixo, após as rotas API)
app.get(['/', '/index.html'], (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'index.html'));
});

app.get('/login.html', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'login.html'));
});

app.get('/register.html', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'register.html'));
});

// Configuração do banco MySQL
const dbConfig = {
  host: process.env.DB_HOST || 'localhost',
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || 'root',
  database: process.env.DB_NAME || 'estoque_db'
};

let pool;

// Helpers para hash/compare de senhas (suporta bcrypt, bcryptjs ou fallback plaintext)
async function hashPassword(password) {
  if (!bcrypt) return password;
  // bcrypt.hash pode retornar Promise (bcrypt) ou aceitar callback (bcryptjs)
  if (typeof bcrypt.hash === 'function') {
    // bcrypt (native) supports Promise
    try {
      return await bcrypt.hash(password, 10);
    } catch (err) {
      // fallback para sync
      if (typeof bcrypt.hashSync === 'function') return bcrypt.hashSync(password, 10);
    }
  }
  if (typeof bcrypt.hashSync === 'function') return bcrypt.hashSync(password, 10);
  return password;
}

async function comparePassword(password, hash) {
  if (!bcrypt) return password === hash;
  if (typeof bcrypt.compare === 'function') {
    try {
      return await bcrypt.compare(password, hash);
    } catch (err) {
      if (typeof bcrypt.compareSync === 'function') return bcrypt.compareSync(password, hash);
    }
  }
  if (typeof bcrypt.compareSync === 'function') return bcrypt.compareSync(password, hash);
  return password === hash;
}

async function initializeDb() {
  // Criar conexão sem banco para criar o banco se não existir
  const connection = await mysql.createConnection({
    host: dbConfig.host,
    user: dbConfig.user,
    password: dbConfig.password
  });

  await connection.query(`CREATE DATABASE IF NOT EXISTS \`${dbConfig.database}\``);
  await connection.end();

  pool = await mysql.createPool(dbConfig);

  // Criar tabelas se não existirem
  await pool.query(`
    CREATE TABLE IF NOT EXISTS users (
      id INT AUTO_INCREMENT PRIMARY KEY,
      username VARCHAR(255) UNIQUE NOT NULL,
      password VARCHAR(255) NOT NULL,
      role VARCHAR(50) NOT NULL
    )
  `);

  await pool.query(`
    CREATE TABLE IF NOT EXISTS estoque (
      id INT AUTO_INCREMENT PRIMARY KEY,
      nome VARCHAR(255) UNIQUE NOT NULL,
      quantidade INT NOT NULL,
      qtd_minima INT DEFAULT 0,
      categoria VARCHAR(255),
      fornecedor VARCHAR(255),
      validade DATE,
      preco_custo DECIMAL(10,2),
      preco_venda DECIMAL(10,2),
      codigo_barras VARCHAR(50),
      unidade_medida VARCHAR(20),
      peso_volume VARCHAR(50),
      marca VARCHAR(255),
      localizacao VARCHAR(255)
    )
  `);

  // Garantir que todas as colunas existam no estoque (ALTER se necessário, compatível com MySQL antigo)
  const columnsToAdd = [
    { name: 'preco_custo', def: 'DECIMAL(10,2)' },
    { name: 'preco_venda', def: 'DECIMAL(10,2)' },
    { name: 'codigo_barras', def: 'VARCHAR(50)' },
    { name: 'unidade_medida', def: 'VARCHAR(20)' },
    { name: 'peso_volume', def: 'VARCHAR(50)' },
    { name: 'marca', def: 'VARCHAR(255)' },
    { name: 'localizacao', def: 'VARCHAR(255)' }
  ];
  for (const col of columnsToAdd) {
    try {
      const [existing] = await pool.query(`SHOW COLUMNS FROM estoque LIKE '${col.name}'`);
      if (existing.length === 0) {
        await pool.query(`ALTER TABLE estoque ADD COLUMN ${col.name} ${col.def}`);
        console.log(`Coluna ${col.name} adicionada em estoque.`);
      } else {
        console.log(`Coluna ${col.name} já existe em estoque.`);
      }
    } catch (err) {
      console.warn(`Aviso ao verificar/adicionar coluna ${col.name}:`, err.message);
    }
  }

  await pool.query(`
    CREATE TABLE IF NOT EXISTS relatorio (
      id INT AUTO_INCREMENT PRIMARY KEY,
      nome VARCHAR(255) NOT NULL,
      quantidade INT NOT NULL,
      responsavel VARCHAR(255) NOT NULL,
      motivo VARCHAR(255) NOT NULL,
      data DATETIME NOT NULL
    )
  `);

  // Após garantir tabelas, garantir o usuário admin
  await ensureAdminUser();

  // Seed dados de teste no estoque se vazio
  const [estoqueRows] = await pool.query('SELECT COUNT(*) as cnt FROM estoque');
  if (estoqueRows[0].cnt === 0) {
    await pool.query(`
      INSERT INTO estoque (nome, quantidade, qtd_minima, categoria, fornecedor, localizacao) VALUES
      ('Arroz', 50, 10, 'Alimentos', 'Fornecedor A', 'Prateleira 1'),
      ('Feijão', 30, 5, 'Alimentos', 'Fornecedor B', 'Prateleira 2')
    `);
    console.log('Dados de teste adicionados ao estoque.');
  }
}

// Seed: criar usuário admin padrão se não existir (valores podem vir do .env)
async function ensureAdminUser() {
  const adminUser = process.env.ADMIN_USER || 'admin';
  const adminPass = process.env.ADMIN_PASS || '1234';
  const adminRole = process.env.ADMIN_ROLE || 'admin';
  try {
    const [rows] = await pool.query('SELECT id FROM users WHERE username = ?', [adminUser]);
    if (rows.length === 0) {
      const hashed = await hashPassword(adminPass);
      await pool.query('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', [adminUser, hashed, adminRole]);
      console.log(`Usuario admin criado: ${adminUser}`);
    } else {
      console.log('Usuario admin já existe, pulando seed.');
    }
  } catch (err) {
    console.error('Erro ao garantir usuário admin:', err);
  }
}

// Registro de usuário
app.post('/api/register', async (req, res) => {
  const { username, password, role } = req.body;
  if (!username || !password || !role) {
    return res.status(400).json({ error: 'Campos obrigatórios faltando' });
  }
  try {
      const hashed = await hashPassword(password);
    const [result] = await pool.query('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', [username, hashed, role]);
    res.json({ message: 'Usuário registrado com sucesso' });
  } catch (err) {
    console.error('Erro em /api/register:', err);
    if (err.code === 'ER_DUP_ENTRY') {
      res.status(409).json({ error: 'Usuário já existe' });
    } else {
      res.status(500).json({ error: 'Erro no servidor' });
    }
  }
});

// Login de usuário
app.post('/api/login', async (req, res) => {
  const { username, password } = req.body;
  if (!username || !password) {
    return res.status(400).json({ error: 'Campos obrigatórios faltando' });
  }
  try {
      const [rows] = await pool.query('SELECT username, password, role FROM users WHERE username = ?', [username]);
    if (rows.length === 1) {
      const user = rows[0];
    const ok = await comparePassword(password, user.password);
    if (ok) {
        // Autenticado
        res.json({ username: user.username, role: user.role });
      } else {
        res.status(401).json({ error: 'Usuário ou senha incorretos' });
      }
    } else {
      res.status(401).json({ error: 'Usuário ou senha incorretos' });
    }
  } catch (err) {
    console.error('Erro em /api/login:', err);
    res.status(500).json({ error: 'Erro no servidor' });
  }
});

// Obter lista de usuários (admin)
app.get('/api/users', async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT username, role FROM users');
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: 'Erro no servidor' });
  }
});

// Editar usuário (username, password, role)
app.put('/api/users/:username', async (req, res) => {
  const oldUsername = req.params.username;
  const { username: newUsername, password, role } = req.body;
  try {
    const [rows] = await pool.query('SELECT * FROM users WHERE username = ?', [oldUsername]);
    if (rows.length !== 1) return res.status(404).json({ error: 'Usuário não encontrado' });
    const user = rows[0];

    // Prevent removing last admin via role change
    if (user.role === 'admin' && role && role !== 'admin') {
      const [admins] = await pool.query('SELECT COUNT(*) as cnt FROM users WHERE role = ?', ['admin']);
      if (admins[0].cnt <= 1) return res.status(400).json({ error: 'Não é permitido remover o último usuário admin' });
    }

    // Check username conflict
    if (newUsername && newUsername !== oldUsername) {
      const [existing] = await pool.query('SELECT id FROM users WHERE username = ?', [newUsername]);
      if (existing.length > 0) return res.status(409).json({ error: 'Nome de usuário já em uso' });
    }

    const updates = [];
    const params = [];
    if (newUsername) {
      updates.push('username = ?');
      params.push(newUsername);
    }
    if (typeof role !== 'undefined') {
      updates.push('role = ?');
      params.push(role);
    }
    if (password) {
      const hashed = await hashPassword(password);
      updates.push('password = ?');
      params.push(hashed);
    }

    if (updates.length === 0) return res.json({ message: 'Nada a atualizar' });

    params.push(oldUsername);
    const sql = `UPDATE users SET ${updates.join(', ')} WHERE username = ?`;
    await pool.query(sql, params);
    res.json({ message: 'Usuário atualizado com sucesso' });
  } catch (err) {
    console.error('Erro em PUT /api/users/:username', err);
    res.status(500).json({ error: 'Erro no servidor' });
  }
});

// Deletar usuário
app.delete('/api/users/:username', async (req, res) => {
  const username = req.params.username;
  try {
    const [rows] = await pool.query('SELECT role FROM users WHERE username = ?', [username]);
    if (rows.length !== 1) return res.status(404).json({ error: 'Usuário não encontrado' });
    const role = rows[0].role;
    if (role === 'admin') {
      const [admins] = await pool.query('SELECT COUNT(*) as cnt FROM users WHERE role = ?', ['admin']);
      if (admins[0].cnt <= 1) return res.status(400).json({ error: 'Não é permitido deletar o último usuário admin' });
    }
    await pool.query('DELETE FROM users WHERE username = ?', [username]);
    res.json({ message: 'Usuário removido com sucesso' });
  } catch (err) {
    console.error('Erro em DELETE /api/users/:username', err);
    res.status(500).json({ error: 'Erro no servidor' });
  }
});

// Adicionar ou atualizar item no estoque
// Valida entrada básica e adiciona/atualiza produto no banco
app.post('/api/estoque', async (req, res) => {
  const {
    nome, quantidade, qtd_minima, categoria, fornecedor, validade,
    preco_custo, preco_venda, codigo_barras, unidade_medida,
    peso_volume, marca, localizacao
  } = req.body;

  // Validação básica de entrada
  if (!nome || quantidade == null) {
    return res.status(400).json({ error: 'Campos obrigatórios faltando: nome e quantidade' });
  }
  if (typeof quantidade !== 'number' || quantidade < 0) {
    return res.status(400).json({ error: 'Quantidade deve ser um número positivo' });
  }
  if (qtd_minima != null && (typeof qtd_minima !== 'number' || qtd_minima < 0)) {
    return res.status(400).json({ error: 'Quantidade mínima deve ser um número positivo ou nulo' });
  }
  if (preco_custo != null && (typeof preco_custo !== 'number' || preco_custo < 0)) {
    return res.status(400).json({ error: 'Preço de custo deve ser um número positivo ou nulo' });
  }
  if (preco_venda != null && (typeof preco_venda !== 'number' || preco_venda < 0)) {
    return res.status(400).json({ error: 'Preço de venda deve ser um número positivo ou nulo' });
  }
  if (validade && isNaN(Date.parse(validade))) {
    return res.status(400).json({ error: 'Data de validade inválida' });
  }

  // Handle empty strings as null for optional fields
  const safePrecoCusto = preco_custo === '' || preco_custo == null ? null : preco_custo;
  const safePrecoVenda = preco_venda === '' || preco_venda == null ? null : preco_venda;

  // Format date from 'dd/mm/yyyy' to 'yyyy-mm-dd' for MySQL
  let formattedValidade = null;
  if (validade && validade !== '') {
    const parts = validade.split('/');
    if (parts.length === 3) {
      const day = parts[0].padStart(2, '0');
      const month = parts[1].padStart(2, '0');
      const year = parts[2];
      formattedValidade = `${year}-${month}-${day}`;
      // Validate formatted date
      if (isNaN(Date.parse(formattedValidade))) {
        return res.status(400).json({ error: 'Data de validade inválida' });
      }
    } else {
      formattedValidade = validade; // Fallback if already in correct format
    }
  }
  const safeValidade = formattedValidade;

  try {
    const [rows] = await pool.query('SELECT id FROM estoque WHERE nome = ?', [nome]);
    if (rows.length === 1) {
      // Atualizar item existente: adicionar à quantidade e atualizar outros campos
      await pool.query(
        `UPDATE estoque SET
          quantidade = quantidade + ?,
          qtd_minima = ?,
          categoria = ?,
          fornecedor = ?,
          validade = ?,
          preco_custo = ?,
          preco_venda = ?,
          codigo_barras = ?,
          unidade_medida = ?,
          peso_volume = ?,
          marca = ?,
          localizacao = ?
        WHERE nome = ?`,
        [
          quantidade,
          qtd_minima || 0,
          categoria || null,
          fornecedor || null,
          safeValidade,
          safePrecoCusto,
          safePrecoVenda,
          codigo_barras || null,
          unidade_medida || null,
          peso_volume || null,
          marca || null,
          localizacao || null,
          nome
        ]
      );
    } else {
      // Inserir novo item
      await pool.query(
        `INSERT INTO estoque (
          nome, quantidade, qtd_minima, categoria, fornecedor, validade,
          preco_custo, preco_venda, codigo_barras, unidade_medida,
          peso_volume, marca, localizacao
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [
          nome,
          quantidade,
          qtd_minima || 0,
          categoria || null,
          fornecedor || null,
          safeValidade,
          safePrecoCusto,
          safePrecoVenda,
          codigo_barras || null,
          unidade_medida || null,
          peso_volume || null,
          marca || null,
          localizacao || null
        ]
      );
    }
    // Resposta de sucesso (movida para fora do if-else para cobrir ambos os casos)
    res.json({ message: 'Item adicionado/atualizado com sucesso' });
  } catch (err) {
    console.error('Erro em POST /api/estoque:', err);
    res.status(500).json({ error: 'Erro no servidor: ' + err.message });
  }
});

// Obter lista completa de itens no estoque
app.get('/api/estoque', async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT * FROM estoque');
    res.json(rows);
  } catch (err) {
    console.error('Erro em GET /api/estoque:', err);
    res.status(500).json({ error: 'Erro no servidor' });
  }
});

// Remover item do estoque pelo nome
app.delete('/api/estoque/:nome', async (req, res) => {
  const nome = req.params.nome;
  if (!nome) {
    return res.status(400).json({ error: 'Nome do produto é obrigatório' });
  }
  try {
    const [result] = await pool.query('DELETE FROM estoque WHERE nome = ?', [nome]);
    if (result.affectedRows === 0) {
      return res.status(404).json({ error: 'Produto não encontrado' });
    }
    res.json({ message: 'Item removido com sucesso' });
  } catch (err) {
    console.error('Erro em DELETE /api/estoque/:nome:', err);
    res.status(500).json({ error: 'Erro no servidor' });
  }
});

app.put('/api/estoque/:nome', async (req, res) => {
  const nome = req.params.nome;
  const {
    nome: novoNome, quantidade, qtd_minima, categoria, fornecedor, localizacao,
    validade, preco_custo, preco_venda, codigo_barras, unidade_medida,
    peso_volume, marca
  } = req.body;
  if (!nome) {
    return res.status(400).json({ error: 'Nome do produto é obrigatório' });
  }
  // Validação básica
  if (quantidade != null && (typeof quantidade !== 'number' || quantidade < 0)) {
    return res.status(400).json({ error: 'Quantidade deve ser um número positivo' });
  }
  if (qtd_minima != null && (typeof qtd_minima !== 'number' || qtd_minima < 0)) {
    return res.status(400).json({ error: 'Quantidade mínima deve ser um número positivo' });
  }
  if (preco_custo != null && (typeof preco_custo !== 'number' || preco_custo < 0)) {
    return res.status(400).json({ error: 'Preço de custo deve ser um número positivo' });
  }
  if (preco_venda != null && (typeof preco_venda !== 'number' || preco_venda < 0)) {
    return res.status(400).json({ error: 'Preço de venda deve ser um número positivo' });
  }
  if (validade && isNaN(Date.parse(validade))) {
    return res.status(400).json({ error: 'Data de validade inválida' });
  }

  // Handle empty strings as null
  const safePrecoCusto = preco_custo === '' || preco_custo == null ? null : preco_custo;
  const safePrecoVenda = preco_venda === '' || preco_venda == null ? null : preco_venda;

  // Format date from 'dd/mm/yyyy' to 'yyyy-mm-dd' for MySQL
  let formattedValidade = null;
  if (validade && validade !== '') {
    const parts = validade.split('/');
    if (parts.length === 3) {
      const day = parts[0].padStart(2, '0');
      const month = parts[1].padStart(2, '0');
      const year = parts[2];
      formattedValidade = `${year}-${month}-${day}`;
      // Validate formatted date
      if (isNaN(Date.parse(formattedValidade))) {
        return res.status(400).json({ error: 'Data de validade inválida' });
      }
    } else {
      formattedValidade = validade; // Fallback if already in correct format
    }
  }
  const safeValidade = formattedValidade;

  try {
    const [rows] = await pool.query('SELECT * FROM estoque WHERE nome = ?', [nome]);
    if (rows.length !== 1) {
      return res.status(404).json({ error: 'Produto não encontrado' });
    }
    const existing = rows[0];
    // Verificar conflito de nome se novoNome for fornecido
    if (novoNome && novoNome !== nome) {
      const [existingName] = await pool.query('SELECT id FROM estoque WHERE nome = ?', [novoNome]);
      if (existingName.length > 0) {
        return res.status(409).json({ error: 'Nome do produto já em uso' });
      }
    }
    await pool.query(
      `UPDATE estoque SET
        nome = ?,
        quantidade = COALESCE(?, quantidade),
        qtd_minima = COALESCE(?, qtd_minima),
        categoria = COALESCE(?, categoria),
        fornecedor = COALESCE(?, fornecedor),
        localizacao = COALESCE(?, localizacao),
        validade = ?,
        preco_custo = ?,
        preco_venda = ?,
        codigo_barras = COALESCE(?, codigo_barras),
        unidade_medida = COALESCE(?, unidade_medida),
        peso_volume = COALESCE(?, peso_volume),
        marca = COALESCE(?, marca)
      WHERE nome = ?`,
      [
        novoNome || nome,
        quantidade,
        qtd_minima,
        categoria,
        fornecedor,
        localizacao,
        safeValidade || existing.validade,
        safePrecoCusto || existing.preco_custo,
        safePrecoVenda || existing.preco_venda,
        codigo_barras,
        unidade_medida,
        peso_volume,
        marca,
        nome
      ]
    );
    res.json({ message: 'Produto editado com sucesso' });
  } catch (err) {
    console.error('Erro em PUT /api/estoque/:nome:', err);
    res.status(500).json({ error: 'Erro no servidor: ' + err.message });
  }
});

// Registrar retirada de produto: atualiza estoque e registra no relatório
app.post('/api/retirada', async (req, res) => {
  const { nome, quantidade, responsavel, motivo } = req.body;
  if (!nome || quantidade == null || !responsavel || !motivo) {
    return res.status(400).json({ error: 'Campos obrigatórios faltando: nome, quantidade, responsavel, motivo' });
  }
  if (typeof quantidade !== 'number' || quantidade <= 0) {
    return res.status(400).json({ error: 'Quantidade deve ser um número positivo' });
  }
  try {
    // Verificar se produto existe e tem quantidade suficiente
    const [rows] = await pool.query('SELECT quantidade FROM estoque WHERE nome = ?', [nome]);
    if (rows.length !== 1) {
      return res.status(404).json({ error: 'Produto não encontrado' });
    }
    if (rows[0].quantidade < quantidade) {
      return res.status(400).json({ error: 'Quantidade insuficiente no estoque' });
    }
    // Atualizar estoque
    await pool.query('UPDATE estoque SET quantidade = quantidade - ? WHERE nome = ?', [quantidade, nome]);
    // Inserir no relatório
    await pool.query('INSERT INTO relatorio (nome, quantidade, responsavel, motivo, data) VALUES (?, ?, ?, ?, NOW())', [nome, quantidade, responsavel, motivo]);
    res.json({ message: 'Retirada registrada com sucesso' });
  } catch (err) {
    console.error('Erro em POST /api/retirada:', err);
    res.status(500).json({ error: 'Erro no servidor' });
  }
});

// Obter relatório de retiradas ordenado por data decrescente
app.get('/api/relatorio', async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT * FROM relatorio ORDER BY data DESC');
    res.json(rows);
  } catch (err) {
    console.error('Erro em GET /api/relatorio:', err);
    res.status(500).json({ error: 'Erro no servidor' });
  }
});

// Limpar todo o histórico de retiradas (apagar todas as entradas)
app.delete('/api/relatorio', async (req, res) => {
  try {
    await pool.query('DELETE FROM relatorio');
    res.json({ message: 'Histórico apagado com sucesso' });
  } catch (err) {
    console.error('Erro em DELETE /api/relatorio:', err);
    res.status(500).json({ error: 'Erro no servidor' });
  }
});

initializeDb().then(() => {
  // Serve arquivos estáticos do frontend (depois de registrar todas as rotas API)
  app.use(express.static(path.join(__dirname, '..'))); // Serve arquivos estáticos da pasta pai (HTML/CSS/JS do frontend)

  app.listen(port, () => {
    console.log(`Servidor rodando em http://localhost:${port}`);
  });
}).catch(err => {
  console.error('Erro ao inicializar banco:', err);
});
