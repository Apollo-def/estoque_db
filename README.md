# Sistema de Gerenciamento de Estoque

Uma aplicação web simples para gerenciar estoque/inventário com autenticação básica de usuários. Este repositório contém um frontend estático (HTML/CSS/JS) e um backend em Node.js + Express que se conecta a um banco MySQL.
# Sistema de Gerenciamento de Estoque

Aplicação web simples para gerenciar estoque (frontend estático + backend em Node.js/Express) com suporte a registro/login, movimentações (entrada/saída), edição e exclusão de produtos.

Este README foi atualizado para incluir instruções claras de instalação no Windows (PowerShell), configuração via variáveis de ambiente, detalhes sobre endpoints e dicas de segurança.

## Sumário
- Pré-requisitos
- Instalação e configuração (.env)
- Executando no Windows (PowerShell)
- Endpoints e exemplos
- Notas de segurança e operação
- Troubleshooting rápido

## Pré-requisitos

- Node.js (recomendo v16+)
- MySQL (ou MariaDB compatível)
- Git (opcional)

## Estrutura do projeto

- `backend/` — servidor Node.js (contém `server.js`, `package.json`)
- arquivos na raiz — frontend estático: `index.html`, `login.html`, `register.html`, `script.js`, `auth.js`, `style.css`, `login.css`

## Configuração (.env)

O servidor usa variáveis de ambiente para credenciais do banco e porta. Para desenvolvimento, crie um arquivo `backend/.env` (não comitar esse arquivo). Um exemplo está disponível em `backend/.env.example`.

Exemplo mínimo (`backend/.env`):

DB_HOST=localhost
DB_USER=root
DB_PASSWORD=root
DB_NAME=estoque_db
PORT=3000

Observação: substitua `root` por um usuário com senha forte em produção.

## Instalação (backend)

1. Abra um terminal e vá para a pasta do backend:

```powershell
cd 'c:\Users\aluno\Desktop\Nova pasta\backend'
```

2. Instale dependências:

```powershell
npm install
```

Problema comum no Windows PowerShell: se ao rodar `npm install` você receber um erro relacionado a `npm.ps1` (execução de scripts desabilitada), execute uma das opções abaixo:

- Opção A (recomendada para devs): abra o PowerShell como Administrador e permita scripts no escopo do usuário:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Depois rode novamente:

```powershell
npm install
```

- Opção B: use outro shell (Git Bash, CMD, WSL) e execute `npm install` lá.

3. (Opcional) Instale bibliotecas relevantes ao login seguro, caso não tenham sido instaladas:

```powershell
npm install dotenv bcrypt
```

Se `bcrypt` falhar na instalação (compilações nativas em Windows), o servidor tenta usar `bcryptjs` como fallback. Ainda assim, prefira instalar `bcrypt` se possível.

## Rodando o servidor

No diretório `backend`:

```powershell
node server.js
```

Ou, se o `package.json` tiver script, você pode usar:

```powershell
npm start
```

Abra o navegador em: http://localhost:3000

## Endpoints principais (resumo e exemplos)

Observação: verifique `backend/server.js` para o comportamento exato. Abaixo estão os endpoints usados pelo frontend:

- POST /api/register — registra um usuário
  - Body JSON: { "username": "usuario", "password": "senha", "role": "user" }
  - Retorno: sucesso ou erro. Senhas são armazenadas com hashing quando `bcrypt`/`bcryptjs` está disponível.

- POST /api/login — autentica um usuário
  - Body JSON: { "username": "usuario", "password": "senha" }
  - Retorno: objeto do usuário (sem a senha) ou erro.

- GET /api/users — lista usuários (pode ser usado para debug)

- POST /api/estoque — adiciona / atualiza item no estoque
  - Body JSON exemplo:
    { "nome": "Sabonete", "quantidade": 10, "categoria": "Higiene", "fornecedor": "Acme", "validade": "2025-12-01", "localizacao": "Prateleira A" }

- PUT /api/estoque/:nome — atualiza um item identificado por `nome` (implementado para suportar edição)
  - Body JSON: fields que deseja atualizar (por exemplo, `quantidade`, `categoria`, ...)

- DELETE /api/estoque/:nome — remove item pelo nome

- POST /api/retirada — registra saída (movimentação de saída)
  - Body JSON: { "nome": "Sabonete", "quantidade": 2, "responsavel": "fulano", "motivo": "uso interno" }

- GET /api/relatorio — lista movimentações de saída (relatório)

Exemplo de requisição via PowerShell (register):

```powershell
Invoke-RestMethod -Method POST -Uri http://localhost:3000/api/register -Body (@{username='user1';password='senha123';role='user'} | ConvertTo-Json) -ContentType 'application/json'
```

Se a resposta for um erro 500, olhe o console onde o servidor está rodando para ver o stack trace (o servidor agora loga erros do register/login).

## Notas de segurança e operação

- Use `backend/.env` para suas credenciais e não comite esse arquivo.
- Senhas: o servidor tenta usar `bcrypt` (ou `bcryptjs`) para hashear senhas. Se essas libs não estiverem instaladas, o servidor pode cair para comparação simples — o que não é seguro. Instale `bcrypt`/`bcryptjs` para produção.
- Em produção, restrinja CORS e não permita origens públicas irrestritas.

## Troubleshooting rápido

- Erro ao rodar `npm install` no PowerShell: veja a seção acima (Set-ExecutionPolicy) ou use outro shell.
- Erro 500 ao registrar/logar: verifique o console do servidor; envie o trecho do stack trace para diagnóstico.
- `bcrypt` não instala no Windows: tente usar `bcryptjs` como alternativa ou use WSL/Git Bash.

## O que foi mudado neste repositório recentemente

- Implementado hashing de senhas com fallback para `bcryptjs` quando disponível.
- Rotas de edição (`PUT /api/estoque/:nome`) e exclusão (`DELETE /api/estoque/:nome`) adicionadas no backend.
- Frontend: formulario de Movimentação (entrada/saída), botões de editar/excluir na tabela de produtos e mensagens de erro mais detalhadas na UI.

## Como ajudar / Contribuir

1. Abra uma issue descrevendo o problema ou feature
2. Abra um PR com mudança pequena e foco em testes

## Contato

Se precisar de ajuda para rodar o projeto localmente, cole os logs do servidor (console) e eu te ajudo a interpretar.
