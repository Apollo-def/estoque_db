# Sistema de Gerenciamento de Estoque para Mercearia

![Banner](https://via.placeholder.com/800x200/4F46E5/FFFFFF?text=Sistema+de+Mercearia) <!-- Placeholder para banner; substitua por imagem real se disponível -->

## Descrição

O **Sistema de Gerenciamento de Estoque para Mercearia** é uma aplicação web completa e responsiva desenvolvida para facilitar o controle de estoque em pequenas e médias mercearias. Ele permite o registro e login de usuários, gerenciamento de produtos (adicionar, editar, excluir), controle de movimentações (entradas e saídas), relatórios de estoque e exportação de dados. 

A aplicação é dividida em frontend estático (HTML, CSS, JavaScript) e backend em Node.js com Express.js, utilizando MySQL como banco de dados. Suporta autenticação segura com hashing de senhas (via bcrypt ou bcryptjs) e validações robustas para evitar erros comuns, como formatação de datas e valores nulos.

**Principais Benefícios:**
- Interface intuitiva e moderna, otimizada para desktop e mobile.
- Controle de estoque em tempo real com alertas para itens abaixo do mínimo.
- Relatórios de movimentações para auditoria.
- Fácil instalação e configuração, ideal para iniciantes.

## Funcionalidades

- **Autenticação de Usuários:** Registro, login e gerenciamento de perfis (admin/user) com hashing de senhas.
- **Gerenciamento de Produtos:** Adicionar/atualizar produtos com campos como nome, quantidade, categoria, fornecedor, validade, preços (custo/venda), código de barras, unidade de medida, marca e localização.
- **Movimentações de Estoque:** Registro de entradas (adicionar estoque) e saídas (retiradas), com histórico em relatórios.
- **Relatórios e Análises:** Visualização de estoque atual, itens críticos (abaixo do mínimo), margem de lucro e exportação para CSV.
- **Busca e Paginação:** Filtro por nome/categoria e paginação para grandes listas de produtos.
- **Ações Rápidas:** Botões para edição inline, exclusão e reposição automática de itens baixos.
- **Validações:** Tratamento de erros para datas (formato BR: dd/mm/yyyy), números e campos obrigatórios; compatível com MySQL antigo (sem "IF NOT EXISTS" em ALTER TABLE).

## Tecnologias Utilizadas

- **Backend:** Node.js, Express.js, MySQL2 (com pool de conexões), bcrypt/bcryptjs (hashing), dotenv (variáveis de ambiente).
- **Frontend:** HTML5, CSS3 (com Flexbox/Grid), Vanilla JavaScript (sem frameworks para leveza).
- **Banco de Dados:** MySQL/MariaDB – Tabelas: `users`, `estoque`, `relatorio`.
- **Outros:** CORS para integração frontend-backend, body-parser para JSON.

## Estrutura do Projeto

```
estoque_db/
├── README.md                  # Este arquivo
├── .gitignore                 # Ignora node_modules, .env, etc.
├── index.html                 # Página principal (dashboard após login)
├── login.html                 # Página de login
├── register.html              # Página de registro
├── style.css                  # Estilos principais
├── login.css                  # Estilos da página de login
├── script.js                  # Lógica frontend (SPA navigation, API calls)
├── auth.js                    # Funções de autenticação (localStorage)
├── backend/
│   ├── server.js              # Servidor Express com rotas API
│   ├── package.json           # Dependências Node.js
│   ├── package-lock.json      # Lockfile para dependências
│   └── .env.example           # Exemplo de configuração (copie para .env)
```

## Pré-requisitos

- Node.js (v16 ou superior) – [Download](https://nodejs.org/)
- MySQL Server (v5.7+ ou MariaDB) – [Download](https://dev.mysql.com/downloads/)
- Editor de código (VS Code recomendado)
- Git (opcional, para clonagem)

## Instalação e Configuração

### 1. Clonar o Repositório
```bash
git clone https://github.com/seu-usuario/estoque-mercearia.git  # Ou baixe o ZIP
cd estoque-mercearia
```

### 2. Configurar o Banco de Dados
- Inicie o MySQL e crie o banco (o servidor cria automaticamente se não existir):
  ```sql
  CREATE DATABASE IF NOT EXISTS estoque_db;
  ```
- Credenciais padrão: user `root`, password `root` (altere em produção).

### 3. Configurar Variáveis de Ambiente
Crie `backend/.env` baseado em `backend/.env.example`:
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=root
DB_NAME=estoque_db
PORT=3000
ADMIN_USER=admin
ADMIN_PASS=1234
ADMIN_ROLE=admin
```
- **Segurança:** Nunca commite o `.env`. Use senhas fortes.

### 4. Instalar Dependências (Backend)
No diretório `backend/`:
```bash
npm install
```
- Se bcrypt falhar (Windows), instale `bcryptjs` como fallback: `npm install bcryptjs`.

### 5. Executar o Servidor
No diretório `backend/`:
```bash
node server.js
```
- O servidor inicia em `http://localhost:3000`.
- Acesse `http://localhost:3000/login.html` para login (padrão: admin/1234).

## Uso

1. **Login/Registro:** Acesse `/login.html` ou `/register.html`. Após login, o dashboard carrega automaticamente.
2. **Dashboard (Produtos):** Visualize a tabela de estoque. Use busca, paginação e ações (Editar, Movimentar, Deletar).
3. **Adicionar Produto:** Clique em "+ Novo Produto" – preencha o formulário (validade em dd/mm/yyyy).
4. **Movimentações:** Vá para "Movimentações" para entradas/saídas. Use ações rápidas na sidebar.
5. **Usuários (Admin):** Gerencie contas em "Usuários".
6. **Exportar:** Baixe CSV em "Exportar Dados".

**Exemplo de Fluxo:**
- Login: admin / 1234
- Adicione "Arroz" (quantidade: 50, categoria: Alimentos, validade: 31/12/2025, preco_custo: 5.00, preco_venda: 10.00).
- Retire 10 unidades: Vá para Movimentações, selecione produto, tipo "Saída", quantidade 10, motivo "Venda".
- Verifique relatórios e margens (+100%).

## Documentação da API

Todos os endpoints estão em `/api/*`. Use ferramentas como Postman ou curl.

### Autenticação
- **POST /api/register**  
  Body: `{ "username": "user", "password": "pass", "role": "user" }`  
  Response: `{ "message": "Usuário registrado com sucesso" }` ou erro (409 se duplicado).

- **POST /api/login**  
  Body: `{ "username": "admin", "password": "1234" }`  
  Response: `{ "username": "admin", "role": "admin" }` ou 401 (inválido).

### Estoque
- **GET /api/estoque**  
  Response: Array de produtos (ex: `{ "id": 1, "nome": "Arroz", "quantidade": 50, "preco_venda": 10.00, ... }`).

- **POST /api/estoque**  
  Body: `{ "nome": "Produto", "quantidade": 10, "validade": "31/12/2025", "preco_venda": 15.50, ... }`  
  Adiciona ou atualiza (incrementa quantidade se existir).

- **PUT /api/estoque/:nome**  
  Body: `{ "quantidade": 20, "categoria": "Alimentos" }`  
  Atualiza campos específicos.

- **DELETE /api/estoque/:nome**  
  Remove o produto.

### Movimentações
- **POST /api/retirada**  
  Body: `{ "nome": "Arroz", "quantidade": 5, "responsavel": "João", "motivo": "Venda" }`  
  Decrementa estoque e loga no relatório.

- **GET /api/relatorio**  
  Response: Array de saídas (ex: `{ "nome": "Arroz", "quantidade": 5, "data": "2024-01-01 10:00:00" }`).

- **DELETE /api/relatorio**  
  Limpa todo o histórico.

### Usuários (Admin)
- **GET /api/users** – Lista usuários.
- **PUT /api/users/:username** – Edita (nome, senha, role).
- **DELETE /api/users/:username** – Remove (protege último admin).

**Exemplo com curl:**
```bash
curl -X POST http://localhost:3000/api/estoque \
  -H "Content-Type: application/json" \
  -d '{"nome":"Leite","quantidade":20,"preco_venda":4.50,"validade":"15/03/2025"}'
```

## Capturas de Tela

- **Dashboard de Produtos:** Tabela com colunas (Código, Nome, Categoria, Preço, Quantidade, Validade, Ações). Alertas vermelhos para estoque baixo.
- **Formulário de Novo Produto:** Modal com campos categorizados (obrigatórios: nome, quantidade; opcionais: preços, validade).
- **Movimentações:** Formulário para entrada/saída com resumo do produto selecionado.
- **Login:** Página simples com campos de usuário/senha e link para registro.

(Adicione imagens reais aqui: ex. ![Dashboard](./screenshots/dashboard.png))

## Contribuições

1. Fork o repositório.
2. Crie uma branch: `git checkout -b feature/nova-funcionalidade`.
3. Commit: `git commit -m 'Adiciona nova funcionalidade'`.
4. Push: `git push origin feature/nova-funcionalidade`.
5. Abra um Pull Request.

**Diretrizes:** Mantenha código limpo, adicione testes unitários (se aplicável) e atualize este README.

## Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

## Contato

- **Autor:** [Seu Nome ou GitHub](https://github.com/seu-usuario)
- **Issues:** [Abra uma issue](https://github.com/seu-usuario/estoque-mercearia/issues) para bugs ou sugestões.
- **Suporte:** Para dúvidas de instalação, compartilhe logs do console/terminal.

Obrigado por usar o Sistema de Mercearia! 🚀 Se precisar de customizações, avise.
