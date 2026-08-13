const API_BASE = '';

let token = localStorage.getItem('access_token') || null;
let currentUser = null;
const pollingIntervals = {};

const homePage = document.getElementById('homePage');
const authPage = document.getElementById('authPage');
const dashboard = document.getElementById('dashboard');

const goToLoginBtn = document.getElementById('goToLoginBtn');
const goToSignupBtn = document.getElementById('goToSignupBtn');

const loginForm = document.getElementById('loginForm');
const signupForm = document.getElementById('signupForm');
const loginEmail = document.getElementById('loginEmail');
const loginPassword = document.getElementById('loginPassword');
const loginBtn = document.getElementById('loginBtn');
const signupUsername = document.getElementById('signupUsername');
const signupEmail = document.getElementById('signupEmail');
const signupPassword = document.getElementById('signupPassword');
const signupBtn = document.getElementById('signupBtn');
const authError = document.getElementById('authError');
const signupError = document.getElementById('signupError');
const showSignup = document.getElementById('showSignup');
const showLogin = document.getElementById('showLogin');

const logoutBtn = document.getElementById('logoutBtn');

const balanceCredits = document.getElementById('balanceCredits');
const balanceRubles = document.getElementById('balanceRubles');
const balanceCreditsDetail = document.getElementById('balanceCreditsDetail');
const balanceRublesDetail = document.getElementById('balanceRublesDetail');
const depositAmount = document.getElementById('depositAmount');
const depositBtn = document.getElementById('depositBtn');
const withdrawAmount = document.getElementById('withdrawAmount');
const withdrawBtn = document.getElementById('withdrawBtn');
const balanceMsg = document.getElementById('balanceMsg');

const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');

const transactionsList = document.getElementById('transactionsList');
const tasksList = document.getElementById('tasksList');

const tabButtons = document.querySelectorAll('.nav-tabs button');
const tabPanes = {
    chat: document.getElementById('tab-chat'),
    balance: document.getElementById('tab-balance'),
    transactions: document.getElementById('tab-transactions'),
    tasks: document.getElementById('tab-tasks'),
};

function apiFetch(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...options.headers,
    };
    return fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
    }).then(res => {
        if (!res.ok) {
            return res.json().then(err => { throw new Error(err.detail || 'Ошибка запроса'); });
        }
        return res.json();
    });
}

function showAuthError(msg) {
    authError.textContent = msg;
    signupError.textContent = '';
}

function showSignupError(msg) {
    signupError.textContent = msg;
    authError.textContent = '';
}

function showHomePage() {
    homePage.style.display = 'flex';
    authPage.style.display = 'none';
    dashboard.style.display = 'none';
}

function showAuthPage() {
    homePage.style.display = 'none';
    authPage.style.display = 'flex';
    dashboard.style.display = 'none';
}

function showDashboard() {
    homePage.style.display = 'none';
    authPage.style.display = 'none';
    dashboard.style.display = 'flex';
}

goToLoginBtn.addEventListener('click', () => {
    showAuthPage();
    showLoginForm();
});

goToSignupBtn.addEventListener('click', () => {
    showAuthPage();
    showSignupForm();
});

function handleLogin() {
    const email = loginEmail.value.trim();
    const password = loginPassword.value.trim();
    if (!email || !password) {
        showAuthError('Заполните все поля');
        return;
    }

    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    fetch('/api/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
    })
    .then(res => {
        if (!res.ok) {
            return res.json().then(err => { throw new Error(err.detail || 'Ошибка входа'); });
        }
        return res.json();
    })
    .then(data => {
        if (data.access_token) {
            token = data.access_token;
            localStorage.setItem('access_token', token);
            enterDashboard();
        } else {
            showAuthError('Неверные учётные данные');
        }
    })
    .catch(err => {
        showAuthError(err.message || 'Ошибка входа');
    });
}

function handleSignup() {
    const username = signupUsername.value.trim();
    const email = signupEmail.value.trim();
    const password = signupPassword.value.trim();
    if (!username || !email || !password) {
        showSignupError('Заполните все поля');
        return;
    }
    apiFetch('/api/users/signup', {
        method: 'POST',
        body: JSON.stringify({ username, email, password_hash: password }),
    }).then(data => {
        if (data.message) {
            showLoginForm();
            showSignupError('');
            loginEmail.value = email;
            loginPassword.value = password;
            showAuthError('✅ Регистрация успешна! Войдите.');
        } else {
            showSignupError('Ошибка регистрации');
        }
    }).catch(err => {
        showSignupError(err.message || 'Ошибка регистрации');
    });
}

function showLoginForm() {
    loginForm.style.display = 'block';
    signupForm.style.display = 'none';
    authError.textContent = '';
    signupError.textContent = '';
}

function showSignupForm() {
    loginForm.style.display = 'none';
    signupForm.style.display = 'block';
    authError.textContent = '';
    signupError.textContent = '';
}

showSignup.addEventListener('click', showSignupForm);
showLogin.addEventListener('click', showLoginForm);
loginBtn.addEventListener('click', handleLogin);
signupBtn.addEventListener('click', handleSignup);
loginPassword.addEventListener('keydown', e => { if (e.key === 'Enter') handleLogin(); });
signupPassword.addEventListener('keydown', e => { if (e.key === 'Enter') handleSignup(); });

function enterDashboard() {
    showDashboard();
    refreshBalance();
    loadTransactions();
    loadTasks();
    switchTab('chat');
}

function logout() {
    token = null;
    localStorage.removeItem('access_token');
    showHomePage();
    Object.values(pollingIntervals).forEach(clearInterval);
    chatMessages.innerHTML = `
        <div class="message assistant">
            Здравствуйте! Я — ваш AI-психолог. Чем могу помочь?<br />
            <span class="meta">🤖</span>
        </div>
    `;
}

logoutBtn.addEventListener('click', logout);

function switchTab(tabId) {
    tabButtons.forEach(btn => btn.classList.toggle('active', btn.dataset.tab === tabId));
    Object.keys(tabPanes).forEach(key => {
        tabPanes[key].classList.toggle('active', key === tabId);
    });
    if (tabId === 'balance') refreshBalance();
    if (tabId === 'transactions') loadTransactions();
    if (tabId === 'tasks') loadTasks();
}

tabButtons.forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
});

function refreshBalance() {
    if (!token) return;
    apiFetch('/api/balance/me')
        .then(data => {
            const credits = data.credits || 0;
            const rubles = data.rubles || 0;
            balanceCredits.textContent = credits;
            balanceRubles.textContent = rubles.toFixed(2);
            balanceCreditsDetail.textContent = credits;
            balanceRublesDetail.textContent = rubles.toFixed(2) + ' ₽';
        })
        .catch(err => console.warn('Balance fetch error:', err));
}

depositBtn.addEventListener('click', () => {
    const amount = parseInt(depositAmount.value);
    if (!amount || amount <= 0) {
        balanceMsg.textContent = 'Введите положительное число кредитов';
        return;
    }
    apiFetch('/api/balance/me/deposit', {
        method: 'POST',
        body: JSON.stringify({ credits: amount }),
    })
    .then(data => {
        balanceMsg.textContent = `✅ Пополнено ${amount} кредитов. Новый баланс: ${data.credits} кредитов`;
        refreshBalance();
        depositAmount.value = '';
    })
    .catch(err => {
        balanceMsg.textContent = '❌ ' + (err.message || 'Ошибка пополнения');
    });
});

withdrawBtn.addEventListener('click', () => {
    const amount = parseInt(withdrawAmount.value);
    if (!amount || amount <= 0) {
        balanceMsg.textContent = 'Введите положительное число кредитов';
        return;
    }
    apiFetch('/api/balance/me/withdraw', {
        method: 'POST',
        body: JSON.stringify({ credits: amount }),
    })
    .then(data => {
        balanceMsg.textContent = `✅ Списано ${amount} кредитов. Новый баланс: ${data.credits} кредитов`;
        refreshBalance();
        withdrawAmount.value = '';
    })
    .catch(err => {
        balanceMsg.textContent = '❌ ' + (err.message || 'Ошибка списания');
    });
});

// ===== ЧАТ =====
function appendMessage(role, content, meta = '') {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = content + (meta ? `<span class="meta">${meta}</span>` : '');
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function pollTaskStatus(taskId, onComplete) {
    if (pollingIntervals[taskId]) clearInterval(pollingIntervals[taskId]);
    let attempts = 0;
    const maxAttempts = 30;
    const interval = setInterval(() => {
        attempts++;
        apiFetch(`/api/ml-tasks/${taskId}`)
            .then(task => {
                if (task.status === 'COMPLETED') {
                    clearInterval(interval);
                    delete pollingIntervals[taskId];
                    onComplete(null, task);
                } else if (task.status === 'FAILED' || task.status === 'VALIDATION_ERROR') {
                    clearInterval(interval);
                    delete pollingIntervals[taskId];
                    onComplete(task.error_message || 'Ошибка выполнения', task);
                } else if (attempts >= maxAttempts) {
                    clearInterval(interval);
                    delete pollingIntervals[taskId];
                    onComplete('Превышено время ожидания');
                }
            })
            .catch(() => { /* игнорируем сетевые ошибки */ });
    }, 3000);
    pollingIntervals[taskId] = interval;
}

function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;
    chatInput.value = '';
    appendMessage('user', text);

    sendBtn.disabled = true;
    sendBtn.textContent = 'Отправка...';

    appendMessage('assistant', '⏳ Ожидание ответа...', '🤖');

    apiFetch('/api/ml-tasks/predict', {
        method: 'POST',
        body: JSON.stringify({
            features: { prompt: text },
            model: 'Qwen2.5-1.5B-Instruct'
        }),
    })
    .then(data => {
        const taskId = data.task_id;
        if (!taskId) throw new Error('Не получен ID задачи');
        pollTaskStatus(taskId, (error, task) => {
            sendBtn.disabled = false;
            sendBtn.textContent = 'Отправить';
            const msgs = chatMessages.querySelectorAll('.message.assistant');
            const last = msgs[msgs.length - 1];
            if (last && last.textContent.includes('⏳ Ожидание ответа...')) {
                last.remove();
            }
            if (error) {
                appendMessage('assistant', '❌ Ошибка: ' + error, '🤖');
            } else {
                const response = task?.output_data?.response || 'Ответ не получен';
                appendMessage('assistant', response, '🤖');
                refreshBalance();
            }
            loadTasks();
        });
    })
    .catch(err => {
        sendBtn.disabled = false;
        sendBtn.textContent = 'Отправить';
        const msgs = chatMessages.querySelectorAll('.message.assistant');
        const last = msgs[msgs.length - 1];
        if (last && last.textContent.includes('⏳ Ожидание ответа...')) {
            last.remove();
        }
        appendMessage('assistant', '❌ Ошибка: ' + (err.message || 'Не удалось отправить'), '🤖');
    });
}

sendBtn.addEventListener('click', sendMessage);
chatInput.addEventListener('keydown', e => { if (e.key === 'Enter' && !sendBtn.disabled) sendMessage(); });

function loadTransactions() {
    if (!token) return;
    apiFetch('/api/transactions/me')
        .then(list => {
            transactionsList.innerHTML = '';
            if (!list || list.length === 0) {
                transactionsList.innerHTML = '<div class="empty-state">Нет транзакций</div>';
                return;
            }
            list.forEach(t => {
                const div = document.createElement('div');
                div.className = 'list-item';
                const statusClass = t.status || 'pending';
                div.innerHTML = `
                    <div class="left">
                        <span class="title">${t.transaction_type === 'DEPOSIT' ? '💰 Пополнение' : '💸 Списание'}</span>
                        <span class="sub">${t.description || ''} • ${new Date(t.created_at).toLocaleString()}</span>
                    </div>
                    <div class="right">
                        <span style="color: ${t.transaction_type === 'DEPOSIT' ? '#28a745' : '#dc3545'};">
                            ${t.transaction_type === 'DEPOSIT' ? '+' : '-'}${t.amount} ₽
                        </span>
                        <span class="status-badge ${statusClass}">${statusClass}</span>
                    </div>
                `;
                transactionsList.appendChild(div);
            });
        })
        .catch(err => {
            transactionsList.innerHTML = '<div class="empty-state">Ошибка загрузки транзакций</div>';
            console.warn(err);
        });
}

function loadTasks() {
    if (!token) return;
    apiFetch('/api/ml-tasks/')
        .then(list => {
            tasksList.innerHTML = '';
            if (!list || list.length === 0) {
                tasksList.innerHTML = '<div class="empty-state">Нет задач</div>';
                return;
            }
            list.slice().reverse().forEach(t => {
                const div = document.createElement('div');
                div.className = 'list-item';
                const statusClass = (t.status || 'pending').toLowerCase();
                const prompt = t.input_data?.prompt || '—';
                const response = t.output_data?.response || '';
                const shortResponse = response.length > 80 ? response.slice(0, 80) + '…' : response;
                div.innerHTML = `
                    <div class="left">
                        <span class="title">📝 ${prompt.slice(0, 50)}${prompt.length > 50 ? '…' : ''}</span>
                        <span class="sub">${new Date(t.created_at).toLocaleString()} • Стоимость: ${t.cost} кредитов</span>
                        ${response ? `<span class="sub" style="color: #4a5a6e;">Ответ: ${shortResponse}</span>` : ''}
                    </div>
                    <div class="right">
                        <span class="status-badge ${statusClass}">${statusClass}</span>
                    </div>
                `;
                tasksList.appendChild(div);
            });
        })
        .catch(err => {
            tasksList.innerHTML = '<div class="empty-state">Ошибка загрузки задач</div>';
            console.warn(err);
        });
}

function init() {
    if (token) {
        apiFetch('/api/users/me')
            .then(user => {
                if (user && user.id) {
                    currentUser = user;
                    enterDashboard();
                } else {
                    logout();
                }
            })
            .catch(() => logout());
    } else {
        showHomePage();
    }
}

setInterval(() => {
    if (token) refreshBalance();
}, 30000);

// Запуск
init();