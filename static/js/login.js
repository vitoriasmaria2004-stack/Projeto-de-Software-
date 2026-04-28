const API_BASE = '/api';
const TOKEN_KEY = 'storyflow_token';

const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const toast = document.getElementById('toast');

document.addEventListener('DOMContentLoaded', async () => {
    await tentarSessaoExistente();
    bindForms();
});

function bindForms() {
    loginForm?.addEventListener('submit', async (event) => {
        event.preventDefault();
        const payload = Object.fromEntries(new FormData(loginForm).entries());
        await autenticar('/auth/login', payload, loginForm);
    });

    registerForm?.addEventListener('submit', async (event) => {
        event.preventDefault();
        const payload = Object.fromEntries(new FormData(registerForm).entries());
        await autenticar('/auth/register', payload, registerForm);
    });
}

async function tentarSessaoExistente() {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
        return;
    }
    try {
        await api('/auth/me', {token});
        window.location.href = '/app/inicio';
    } catch (error) {
        localStorage.removeItem(TOKEN_KEY);
    }
}

async function autenticar(path, payload, form) {
    try {
        const response = await api(path, {method: 'POST', body: payload, auth: false});
        localStorage.setItem(TOKEN_KEY, response.token);
        form.reset();
        showToast(response.mensagem || 'Login realizado com sucesso.');
        setTimeout(() => {
            window.location.href = '/app/inicio';
        }, 320);
    } catch (error) {
        showToast(error.message, true);
    }
}

async function api(path, options = {}) {
    const method = options.method || 'GET';
    const headers = {'Accept': 'application/json'};

    if (options.body) {
        headers['Content-Type'] = 'application/json';
    }

    if (options.token) {
        headers.Authorization = `Bearer ${options.token}`;
    }

    const response = await fetch(`${API_BASE}${path}`, {
        method,
        headers,
        body: options.body ? JSON.stringify(options.body) : undefined,
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.sucesso === false) {
        throw new Error(data.erro || 'Não foi possível concluir a autenticação.');
    }
    return data;
}

function showToast(message, error = false) {
    if (!toast) {
        return;
    }
    toast.textContent = message;
    toast.classList.remove('hidden', 'error');
    if (error) {
        toast.classList.add('error');
    }
    clearTimeout(showToast.timer);
    showToast.timer = setTimeout(() => {
        toast.classList.add('hidden');
    }, 2800);
}
