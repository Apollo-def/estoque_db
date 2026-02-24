# Sistema Multi-Tenant de Controle de Estoque Hospitalar

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-red.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple.svg)](https://getbootstrap.com/)

Um sistema web completo e robusto para gestão de estoque hospitalar com arquitetura **Multi-Tenant**, desenvolvido com Flask, Bootstrap 5 e SQLite/PostgreSQL.

O sistema permite que uma única instalação gerencie múltiplas unidades hospitalares, mantendo os dados de estoque, movimentações e configurações completamente isolados entre si.

## 📋 Índice

- [Funcionalidades](#-funcionalidades)
- [Tecnologias](#-tecnologias)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Deploy](#-deploy)
- [Segurança](#-segurança)
- [Scripts Utilitários](#-scripts-utilitários)
- [Solução de Problemas](#-solução-de-problemas)
- [Contribuição](#-contribuição)
- [Licença](#-licença)

---

## 🚀 Funcionalidades

### 🏢 Gestão Multi-Tenant
- **Isolamento Total:** Dados de cada unidade em bancos de dados separados
- **Seleção de Contexto:** Usuários navegam entre unidades permitidas sem relogar
- **Configuração Dinâmica:** Suporte híbrido (SQLite e PostgreSQL)
- **Gerenciamento Centralizado:** Uma interface para gerenciar todas as unidades

### 👥 Gestão de Usuários e Acesso
- **RBAC:** Controle de acesso baseado em papéis (Admin/Usuário)
- **Permissões Granulares:** Controle detalhado de acesso a menus e funções
- **Segurança:** Senhas com hash (Werkzeug) e proteção de sessão
- **Múltiplas Unidades:** Usuários podem ter acesso a várias unidades

### 📦 Controle de Estoque
- **Catálogo:** Produtos, Categorias, Fornecedores e Setores
- **Rastreabilidade:** Entradas e Saídas com registro de Nota Fiscal, Lote e Responsável
- **Alertas:** Notificações visuais para estoque baixo ou zerado
- **Dashboard:** Visão geral com indicadores de desempenho (KPIs)
- **Relatórios:** Visualização de movimentações por período

### 🔄 Movimentações
- **Entrada de Produtos:** Registro de compras e recebimentos
- **Saída de Produtos:** Controle de consumo por setor
- **Histórico Completo:** Rastreamento de todas as operações
- **Validação:** Verificação de estoque disponível antes de saídas

---

## 🛠️ Tecnologias

| Camada | Tecnologia |
|--------|------------|
| Backend | Python 3.9+, Flask, SQLAlchemy |
| Frontend | HTML5, CSS3, Bootstrap 5, JavaScript |
| Banco de Dados | SQLite (Desenvolvimento), PostgreSQL (Produção) |
| Servidor | Flask (Dev), Gunicorn/UWSGI (Prod) |
| Infraestrutura | Docker, Render, Heroku, ngrok |

---

## 📥 Instalação

### Pré-requisitos
- Python 3.9 ou superior
- pip (gerenciador de pacotes Python)
- Git (opcional, para clonagem)

### 1. Clonar o Repositório
```
bash
git clone <seu-repositorio>
cd estoque_db
```

### 2. Criar ambiente virtual
```
bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Instalar dependências
```
bash
pip install -r requirements.txt
```

### 4. Executar a aplicação
```
bash
python app.py
```

A aplicação estará disponível em `http://127.0.0.1:5000`

### 5. Credenciais Padrão
```
Email: admin@hospital.com
Senha: Admin@1234
```

---

## ⚙️ Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Configurações do Flask
SECRET_KEY=sua_chave_secreta_aqui
FLASK_ENV=development
FLASK_DEBUG=1

# Banco de Dados (opcional - usa SQLite por padrão)
DB_ENGINE=sqlite
DB_NAME=central.db

# Configurações de Sessão
PERMANENT_SESSION_LIFETIME=3600
SESSION_COOKIE_SECURE=False
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

### Configuração de Banco de Dados

#### SQLite (Padrão)
O sistema usa SQLite por padrão. Os bancos são armazenados na pasta `instance/`.

#### PostgreSQL (Produção)
Para usar PostgreSQL, configure no `database_config.py`:

```
python
DATABASES = {
    'hospital_sao_paulo': {
        'name': 'Hospital São Paulo',
        'database': 'postgresql://user:password@host:5432/db_name',
        'host': 'your-postgres-host',
        'type': 'postgresql',
        'description': 'Hospital São Paulo - Unidade Central'
    }
}
```

Instale o driver:
```
bash
pip install psycopg2-binary
```

### Configuração de Unidades

Para adicionar novas unidades hospitalares, use a interface administrativa ou o script:

```
bash
python scripts/init_all_dbs.py
```

---

## 🌐 Deploy

### Deploy Local com ngrok

Para expor o servidor local para a internet durante desenvolvimento:

```
bash
# Iniciar o Flask
python app.py

# Em outro terminal, iniciar o ngrok
ngrok http 5000
```

O ngrok fornece uma URL temporária como `https://seu-subdomain.ngrok-free.app`

> **Nota:** O sistema já está configurado com o header `ngrok-skip-browser-warning` para evitar o aviso de browser.

### Deploy no Render.com

1. Crie uma conta no [Render.com](https://render.com)
2. Crie um novo Web Service
3. Conecte seu repositório Git
4. Configure as variáveis de ambiente:
   
```
env
   PYTHON_VERSION=3.9
   SECRET_KEY=sua_chave_secreta
   DATABASE_URL=url_do_postgresql
   
```
5. **Build Command:**
   
```
bash
   pip install -r requirements.txt
   python scripts/init_all_dbs.py
   
```
6. **Start Command:** `python app.py`

### Deploy no Heroku

1. Crie uma app no Heroku
2. Configure o buildpack Python
3. Defina variáveis de ambiente no dashboard
4. Faça deploy via Git ou GitHub

### Deploy com Docker

```
dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python scripts/init_all_dbs.py

EXPOSE 5000
CMD ["python", "app.py"]
```

```
bash
# Build
docker build -t estoque-hospitalar .

# Run
docker run -p 5000:5000 -v $(pwd)/instance:/app/instance estoque-hospitalar
```

---

## 🔐 Segurança

- **Hash de Senhas:** Utiliza Werkzeug para hashing seguro
- **Proteção de Sessão:** Flask-Session com configurações seguras
- **CSRF Protection:** Tokens em todos os formulários
- **Validação de Entrada:** Sanitização de dados do usuário
- **Isolamento de Dados:** Arquitetura multi-tenant com bancos separados
- **Headers de Segurança:** Configuração de headers HTTP seguros

### Boas Práticas de Segurança

1. Altere a `SECRET_KEY` em produção
2. Use HTTPS em ambientes de produção
3. Configure `SESSION_COOKIE_SECURE=True` em produção
4. Mantenha as dependências atualizadas
5. Faça backups regulares dos bancos de dados

---

## 🛠️ Scripts Utilitários

### Gerenciamento de Usuários

| Script | Descrição |
|--------|-----------|
| `make_admin.py` | Cria ou promove usuário para administrador |
| `list_admins.py` | Lista todos os administradores do sistema |
| `grant_units.py` | Concede acesso a unidades para usuários |

**Exemplo de uso:**
```
bash
# Criar administrador
python scripts/make_admin.py admin@hospital.com Admin@1234

# Listar administradores
python scripts/list_admins.py

# Conceder acesso a unidades
python scripts/grant_units.py usuario@email.com "hospital_sao_paulo,hospital_ilha"
```

### Gerenciamento de Banco de Dados

| Script | Descrição |
|--------|-----------|
| `init_all_dbs.py` | Inicializa todos os bancos de dados |
| `inspect_central.py` | Inspeciona o banco central |
| `normalize_unidades_access.py` | Corrige dados de permissões |
| `migrate_db.py` | Executa migrações de banco |

**Exemplo de uso:**
```
bash
# Inicializar bancos
python scripts/init_all_dbs.py

# Normalizar permissões
python scripts/normalize_unidades_access.py

# Inspccionar banco
python scripts/inspect_central.py admin@hospital.com
```

---

## 🔧 Solução de Problemas

### Problemas Comuns

#### Erro JSONDecodeError
```
bash
python scripts/normalize_unidades_access.py
```

#### Problemas de Conexão com Banco
1. Verifique se os arquivos `.db` existem em `instance/`
2. Execute: `python scripts/init_all_dbs.py`
3. Verifique permissões de escrita na pasta

#### Usuário sem acesso às unidades
1. Admin deve acessar `/editar/<id>` do usuário
2. Selecionar as unidades permitidas
3. Salvar as alterações

#### Erro de dependências
```
bash
pip install -r requirements.txt --force-reinstall
```

#### Erro de permissão no Windows
```
bash
# Executar como administrador ou usar virtualenv
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Logs e Debug

- Logs do Flask aparecem no console durante execução
- Use `app.logger.info()` para logging personalizado
- Modo debug: execute `python app.py` (desenvolvimento)

---

## 🤝 Contribuição

Contribuições são bem-vindas! Siga estes passos:

1. **Fork** o projeto
2. **Clone** seu fork: `git clone https://github.com/seu-usuario/estoque_db.git`
3. **Crie** uma branch: `git checkout -b feature/nova-funcionalidade`
4. **Commit** suas mudanças: `git commit -am 'Adiciona nova funcionalidade'`
5. **Push** para a branch: `git push origin feature/nova-funcionalidade`
6. **Abra** um Pull Request

### Diretrizes de Código

- Use **SQLAlchemy** para queries ao banco de dados
- Mantenha **isolamento por tenant** em todas as operações
- Documente **funções e classes** com docstrings
- Siga **PEP 8** para código Python
- Use **commits descritivos** em português ou inglês
- Adicione **testes** para novas funcionalidades

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 🆘 Suporte

### Contato
- **Email:** admin@hospital.com
- **Documentação:** Este README

### Informações Técnicas

| Componente | Descrição |
|------------|------------|
| Arquitetura | Sistema multi-tenant com isolamento por unidade |
| Banco Central | Armazena usuários, unidades e configurações |
| Bancos Tenant | Um banco de dados por unidade hospitalar |
| Sessões | Controle de acesso baseado em permissões |

---

## 📝 Changelog

### Versão 1.0.0
- Sistema multi-tenant funcional
- Gestão de usuários e permissões
- Controle de estoque completo
- Movimentações (entrada/saída)
- Interface administrativa

---

*Desenvolvido para gestão hospitalar - Sistema de Estoque Multi-Tenant*
