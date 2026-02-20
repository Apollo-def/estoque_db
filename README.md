# Sistema Multi-Tenant de Controle de Estoque Hospitalar

!Python
!Flask
!License

Um sistema web completo e robusto para gestão de estoque hospitalar com arquitetura **Multi-Tenant**, desenvolvido com Flask, Bootstrap 5 e SQLite/PostgreSQL.

O sistema permite que uma única instalação gerencie múltiplas unidades hospitalares, mantendo os dados de estoque, movimentações e configurações completamente isolados entre si.

## 🚀 Funcionalidades

### 🏢 Gestão Multi-Tenant
- **Isolamento Total:** Dados de cada unidade em bancos de dados separados.
- **Seleção de Contexto:** Usuários navegam entre unidades permitidas sem relogar.
- **Configuração Dinâmica:** Suporte híbrido (algumas unidades em SQLite, outras em PostgreSQL).

### 👥 Gestão de Usuários e Acesso
- **RBAC:** Controle de acesso baseado em papéis (Admin/Usuário).
- **Permissões Granulares:** Controle detalhado de acesso a menus e funções.
- **Segurança:** Senhas com hash (Werkzeug) e proteção de sessão.

### 📦 Controle de Estoque
- **Catálogo:** Produtos, Categorias, Fornecedores e Setores.
- **Rastreabilidade:** Entradas e Saídas com registro de Nota Fiscal, Lote e Responsável.
- **Alertas:** Notificações visuais para estoque baixo ou zerado.
- **Dashboard:** Visão geral com indicadores de desempenho (KPIs).

## 🛠️ Tecnologias

- **Backend:** Python, Flask, SQLAlchemy.
- **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript.
- **Banco de Dados:** SQLite (Padrão), PostgreSQL (Suportado).
- **Infraestrutura:** Docker, Render, Heroku.

##  Instalação

### 1. Clonar o Repositório
```bash
git clone <seu-repositorio>
cd estoque_db
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