# Sistema Multi-Tenant de Controle de Estoque Hospitalar

Um sistema web completo para gestão de estoque hospitalar com arquitetura multi-tenant, desenvolvido com Flask, Bootstrap e SQLite.

## 🚀 Funcionalidades

### Gestão de Usuários
- ✅ Login e cadastro de usuários
- ✅ Controle de acesso baseado em papéis (Admin/Usuário)
- ✅ Permissões por unidade hospitalar
- ✅ Senhas criptografadas com hash
- ✅ Sessões seguras

### Gestão de Unidades
- ✅ Cadastro de unidades hospitalares
- ✅ Isolamento de dados por tenant
- ✅ Configuração dinâmica de bancos de dados

### Gestão de Produtos
- ✅ Cadastro de produtos com categorias
- ✅ Controle de estoque mínimo
- ✅ Códigos de barras
- ✅ Unidades de medida

### Controle de Movimentações
- ✅ Registro de entradas e saídas
- ✅ Rastreamento de origem/destino
- ✅ Notas fiscais e ordens de serviço
- ✅ Histórico completo

### Relatórios e Dashboard
- ✅ Dashboard com estatísticas
- ✅ Produtos mais movimentados
- ✅ Alertas de estoque baixo
- ✅ Interface responsiva com Bootstrap

## 🛠️ Tecnologias Utilizadas

### Backend
- **Flask** - Framework web Python
- **Flask-SQLAlchemy** - ORM para banco de dados
- **Werkzeug** - Criptografia de senhas

### Frontend
- **HTML5**
- **CSS3**
- **Bootstrap 5** - Framework CSS responsivo
- **Jinja2** - Templates

### Banco de Dados
- **SQLite** - Banco central e por tenant
- **PostgreSQL** - Suporte opcional para produção

### Infraestrutura
- **Arquitetura Multi-Tenant** - Isolamento por unidade
- **Database Manager** - Gerenciamento dinâmico de conexões
- **Tenant DB** - Abstração de acesso aos bancos

## 📁 Estrutura do Projeto

```
sistema-estoque-hospitalar/
│
├── app.py                    # Aplicação principal Flask
├── database_config.py        # Configuração de unidades e bancos
├── database_manager.py       # Gerenciamento de conexões DB
├── tenant_db.py             # Abstração de acesso aos tenants
├── requirements.txt          # Dependências Python
├── README.md                # Documentação
│
├── instance/                # Bancos de dados
│   ├── central.db          # Banco central (usuários, unidades)
│   ├── hospital_*.db       # Bancos por unidade
│
├── scripts/                 # Scripts utilitários
│   ├── init_all_dbs.py     # Inicialização de bancos
│   ├── make_admin.py       # Criação de usuário admin
│   ├── inspect_central.py  # Inspeção do banco central
│   ├── normalize_unidades_access.py # Normalização de permissões
│
├── templates/               # Templates HTML
│   ├── base.html           # Template base
│   ├── login.html          # Página de login
│   ├── cadastro.html       # Página de cadastro
│   ├── index.html          # Dashboard
│   ├── tabela.html         # Gestão de usuários
│   ├── editar.html         # Editar usuário
│   ├── produtos.html       # Gestão de produtos
│   ├── movimentacoes.html  # Controle de movimentações
│   ├── selecionar_unidade.html # Seleção de unidade
│   └── ...
│
├── static/                  # Arquivos estáticos
│   ├── css/
│   ├── js/
│   ├── img/
│   └── scss/
│
└── app/                     # Estrutura modular (opcional)
    ├── models/
    ├── routes/
    ├── forms/
    └── utils/
```

## 📦 Instalação

### 1. Clonar o repositório
```bash
git clone <repositorio>
cd projeto_login
```

### 2. Criar ambiente virtual (recomendado)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Executar a aplicação
```bash
python app.py
```

A aplicação estará disponível em `http://127.0.0.1:5000`

## 🌐 Configuração para Produção

### Banco de Dados PostgreSQL

Para usar PostgreSQL em produção, configure as conexões no `database_config.py`:

```python
DATABASES = {
    'hospital_sao_paulo': {
        'name': 'Hospital São Paulo',
        'database': 'postgresql://user:pass@host:port/db_sao_paulo',
        'host': 'your-postgres-host',
        'type': 'postgresql',
        'description': 'Hospital São Paulo - Unidade Central'
    }
}
```

Instale o driver PostgreSQL:
```bash
pip install psycopg2-binary
```

### Implantação no Render.com

1. Crie uma conta no [Render.com](https://render.com)
2. Crie um novo Web Service
3. Conecte seu repositório Git
4. Configure as variáveis de ambiente:
   - `PYTHON_VERSION`: 3.9
   - `SECRET_KEY`: sua_chave_secreta_aqui
   - `DATABASE_URL`: url_do_banco_postgresql (opcional)
5. Configure o Build Command:
   ```bash
   pip install -r requirements.txt
   python scripts/init_all_dbs.py
   ```
6. Configure o Start Command: `python app.py`

### Implantação no Heroku

1. Crie uma app no Heroku
2. Configure o buildpack Python
3. Defina variáveis de ambiente no dashboard
4. Faça deploy via Git ou GitHub integration

### Implantação com Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python scripts/init_all_dbs.py

EXPOSE 5000
CMD ["python", "app.py"]
```

```bash
docker build -t estoque-hospitalar .
docker run -p 5000:5000 estoque-hospitalar
```

## 🔐 Segurança

- Senhas armazenadas com hash usando Werkzeug
- Sessões seguras com Flask-Session
- Proteção contra CSRF
- Validação de entrada de dados

## 🎨 Personalização

### Alterar cores e estilos
Edite o arquivo `static/style.css` para personalizar o visual da aplicação.

### Modificar templates
Os templates HTML estão na pasta `templates/` e usam a sintaxe Jinja2.

## 📝 Uso

1. **Cadastro**: Acesse `/cadastro` para criar uma nova conta
2. **Login**: Use email e senha para acessar o sistema
3. **Dashboard**: Página inicial após login
4. **Gerenciar Usuários**: Visualize, edite e exclua usuários em `/tabela`

## 🛠️ Scripts Utilitários

### Gerenciamento de Usuários
```bash
# Criar usuário administrador
python scripts/make_admin.py [email] [senha]

# Listar todos os administradores
python scripts/list_admins.py

# Normalizar permissões de unidades (correção de dados)
python scripts/normalize_unidades_access.py
```

### Gerenciamento de Banco de Dados
```bash
# Inicializar todos os bancos de dados
python scripts/init_all_dbs.py

# Inspecionar banco central
python scripts/inspect_central.py [email_opcional]

# Conceder acesso a unidades para usuários
python scripts/grant_units.py
```

## 🔧 Solução de Problemas

### Erro JSONDecodeError
Se encontrar erro ao acessar unidades:
```bash
python scripts/normalize_unidades_access.py
```

### Problemas de Conexão DB
1. Verifique se os arquivos `.db` existem em `instance/`
2. Execute `python scripts/init_all_dbs.py`
3. Verifique permissões de escrita na pasta

### Usuário sem acesso
1. Admin deve editar usuário em `/editar/<id>`
2. Selecionar unidades permitidas
3. Salvar alterações

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

### Diretrizes de Código
- Use SQLAlchemy para queries complexas
- Mantenha isolamento por tenant
- Documente funções e classes
- Siga PEP 8 para Python
- Use commits descritivos

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para detalhes.

## 🆘 Suporte

### Documentação Técnica
- **Arquitetura**: Sistema multi-tenant com isolamento por unidade
- **Banco Central**: Armazena usuários, unidades e configurações
- **Bancos Tenant**: Um por unidade hospitalar
- **Sessões**: Controle de acesso baseado em permissões

### Problemas Comuns
1. **Erro de Python não encontrado**: Reinstale Python e adicione ao PATH
2. **Erro de dependências**: `pip install -r requirements.txt`
3. **Erro de banco**: Execute scripts de inicialização
4. **Erro de permissões**: Verifique configuração de unidades

### Logs e Debug
- Logs do Flask aparecem no console
- Use `app.logger` para logging personalizado
- Debug mode: `python app.py` (desenvolvimento)

---

Email: admin@hospital.com
Senha: Admin@1234



caso eu queira edita ou criar outro Admin 
python scripts/make_admin.py admin@hospital.com Admin@1234