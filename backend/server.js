// server.js - Servidor backend para o Sistema de Gerenciamento de Estoque
// Este arquivo configura um servidor Express.js que fornece APIs para gerenciamento de estoque,
// autenticação de usuários e relatórios, utilizando MySQL como banco de dados.

// Importações de módulos necessários
const express = require('express'); // Framework web para Node.js
const mysql = require('mysql2/promise'); // Cliente MySQL para Node.js com suporte a Promises
const bodyParser = require('body-parser'); // Middleware para parsing de JSON no corpo das requisições
const cors = require('cors'); // Middleware para habilitar CORS (Cross-Origin Resource Sharing)

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
      localizacao VARCHAR(255)
    )
  `);

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
app.post('/api/estoque', async (req, res) => {
  const { nome, quantidade, qtd_minima, categoria, fornecedor, validade, localizacao } = req.body;
  if (!nome || quantidade == null) {
    return res.status(400).json({ error: 'Campos obrigatórios faltando' });
  }
  try {
    const [rows] = await pool.query('SELECT id FROM estoque WHERE nome = ?', [nome]);
    if (rows.length === 1) {
      await pool.query('UPDATE estoque SET quantidade = quantidade + ?, qtd_minima = ?, categoria = ?, fornecedor = ?, validade = ?, localizacao = ? WHERE nome = ?', [quantidade, qtd_minima || 0, categoria, fornecedor, validade, localizacao, nome]);
    } else {
      await pool.query('INSERT INTO estoque (nome, quantidade, qtd_minima, categoria, fornecedor, validade, localizacao) VALUES (?, ?, ?, ?, ?, ?, ?)', [nome, quantidade, qtd_minima || 0, categoria, fornecedor, validade, localizacao]);
    }
    res.json({ message: 'Item adicionado/atualizado com sucesso' });
  } catch (err) {
    res.status(500).json({ error: 'Erro no servidor' });
  }
});

// Obter estoque
app.get('/api/estoque', async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT * FROM estoque');
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: 'Erro no servidor' });
  }
});

// Remover item do estoque
app.delete('/api/estoque/:nome', async (req, res) => {
  const nome = req.params.nome;
  try {
    await pool.query('DELETE FROM estoque WHERE nome = ?', [nome]);
    res.json({ message: 'Item removido com sucesso' });
  } catch (err) {
    res.status(500).json({ error: 'Erro no servidor' });
  }
});

// Editar item do estoque
app.put('/api/estoque/:nome', async (req, res) => {
  const nome = req.params.nome;
  const { nome: novoNome, quantidade, qtd_minima, categoria, fornecedor, localizacao } = req.body;
  try {
    const [rows] = await pool.query('SELECT id FROM estoque WHERE nome = ?', [nome]);
    if (rows.length !== 1) {
      return res.status(404).json({ error: 'Produto não encontrado' });
    }
    await pool.query(
      'UPDATE estoque SET nome = ?, quantidade = ?, qtd_minima = ?, categoria = ?, fornecedor = ?, localizacao = ? WHERE nome = ?',
      [novoNome, quantidade, qtd_minima, categoria, fornecedor, localizacao, nome]
    );
    res.json({ message: 'Produto editado com sucesso' });
  } catch (err) {
    res.status(500).json({ error: 'Erro no servidor' });
  }
});

// Registrar retirada no relatório e atualizar estoque
app.post('/api/retirada', async (req, res) => {
  const { nome, quantidade, responsavel, motivo } = req.body;
  if (!nome || !quantidade || !responsavel || !motivo) {
    return res.status(400).json({ error: 'Campos obrigatórios faltando' });
  }
  try {
    // Atualizar estoque
    const [rows] = await pool.query('SELECT quantidade FROM estoque WHERE nome = ?', [nome]);
    if (rows.length !== 1 || rows[0].quantidade < quantidade) {
      return res.status(400).json({ error: 'Quantidade insuficiente no estoque' });
    }
    await pool.query('UPDATE estoque SET quantidade = quantidade - ? WHERE nome = ?', [quantidade, nome]);
    // Inserir no relatório
    await pool.query('INSERT INTO relatorio (nome, quantidade, responsavel, motivo, data) VALUES (?, ?, ?, ?, NOW())', [nome, quantidade, responsavel, motivo]);
    res.json({ message: 'Retirada registrada com sucesso' });
  } catch (err) {
    res.status(500).json({ error: 'Erro no servidor' });
  }
});

// Obter relatório de retiradas
app.get('/api/relatorio', async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT * FROM relatorio ORDER BY data DESC');
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: 'Erro no servidor' });
  }
});

// Limpar histórico de retiradas
app.delete('/api/relatorio', async (req, res) => {
  try {
    await pool.query('DELETE FROM relatorio');
    res.json({ message: 'Histórico apagado com sucesso' });
  } catch (err) {
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
