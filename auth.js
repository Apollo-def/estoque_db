/**
 * Script para login e registro de usuários
 * Controla a submissão dos formulários de login e registro,
 * faz requisições para o backend e gerencia mensagens de erro/sucesso.
 */

// Login form elements
const loginForm = document.getElementById('loginForm');
const loginError = document.getElementById('loginError');

if (loginForm) {
  // Evento de submissão do formulário de login
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (loginError) loginError.textContent = ''; // Limpa mensagens de erro anteriores
    const username = loginForm.username.value.trim();
    const password = loginForm.password.value.trim();

    try {
      // Envia requisição POST para /api/login com username e password
      const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (res.ok) {
        // Se login for bem-sucedido, armazena dados do usuário no localStorage
        const data = await res.json();
        localStorage.setItem('user', JSON.stringify(data));
        // Redireciona para a página principal
        window.location.href = 'index.html';
      } else {
        // Se erro, exibe mensagem de erro retornada pelo backend (tenta JSON, senão texto)
        let errText = 'Erro no login';
        try {
          const err = await res.json();
          errText = err.error || JSON.stringify(err) || errText;
        } catch (e) {
          try {
            errText = await res.text();
          } catch (e2) {
            // keep default
          }
        }
        if (loginError) loginError.textContent = errText;
      }
    } catch (error) {
      // Erro na comunicação com o servidor
      if (loginError) loginError.textContent = 'Erro na comunicação com o servidor';
    }
  });
}

// Registro form elements
const registerForm = document.getElementById('registerForm');
const registerError = document.getElementById('registerError');
const registerSuccess = document.getElementById('registerSuccess');

if (registerForm) {
  // Evento de submissão do formulário de registro
  registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (registerError) registerError.textContent = ''; // Limpa mensagens de erro anteriores
    if (registerSuccess) registerSuccess.textContent = ''; // Limpa mensagens de sucesso anteriores
    const username = registerForm.regUsername.value.trim();
    const password = registerForm.regPassword.value.trim();
    const role = registerForm.regRole.value;

    try {
      // Envia requisição POST para /api/register com dados do novo usuário
      const res = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, role }),
      });
      if (res.ok) {
        // Exibe mensagem de sucesso e reseta o formulário
        if (registerSuccess) registerSuccess.textContent = 'Usuário registrado com sucesso! Você pode fazer login.';
        registerForm.reset();
      } else {
        // Exibe mensagem de erro retornada pelo backend (tenta JSON, senão texto)
        let errText = 'Erro no registro';
        try {
          const err = await res.json();
          errText = err.error || JSON.stringify(err) || errText;
        } catch (e) {
          try {
            errText = await res.text();
          } catch (e2) {
            // keep default
          }
        }
        if (registerError) registerError.textContent = errText;
      }
    } catch (error) {
      // Erro na comunicação com o servidor
      if (registerError) registerError.textContent = 'Erro na comunicação com o servidor';
    }
  });
}