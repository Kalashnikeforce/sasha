let currentUser = null;
let isAdmin = false;

console.log('🚀 Script.js loaded successfully');

// Railway-specific fixes
window.addEventListener('load', function() {
    console.log('✅ Page loaded, initializing...');
    initializeApp();
});

// Initialize Telegram Web App
if (window.Telegram && window.Telegram.WebApp) {
    window.Telegram.WebApp.ready();
    window.Telegram.WebApp.expand();

    // Check version and set colors accordingly
    const tgVersion = window.Telegram.WebApp.version || '6.0';
    const majorVersion = parseFloat(tgVersion);

    if (majorVersion >= 6.1) {
        // For newer versions that support these methods
        try {
            if (window.Telegram.WebApp.setHeaderColor) {
                window.Telegram.WebApp.setHeaderColor('#0a0a0f');
            }
            if (window.Telegram.WebApp.setBackgroundColor) {
                window.Telegram.WebApp.setBackgroundColor('#0a0a0f');
            }
        } catch (e) {
            console.log('Color methods not available:', e.message);
        }
    } else {
        // For version 6.0 and older, use CSS themes instead
        document.documentElement.style.setProperty('--tg-theme-bg-color', '#0a0a0f');
        document.documentElement.style.setProperty('--tg-theme-secondary-bg-color', '#1a1a2e');
    }

    currentUser = window.Telegram.WebApp.initDataUnsafe?.user;
}

// Initialize app with Railway compatibility
async function initializeApp() {
    console.log('🔧 Initializing app...');

    // Check admin status
    if (currentUser && currentUser.id) {
        try {
            const response = await fetch('/api/check-admin', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: currentUser.id })
            });
            const data = await response.json();
            isAdmin = data.is_admin;
            console.log('Admin status:', isAdmin);
            updateAdminUI();
        } catch (error) {
            console.error('Error checking admin status:', error);
        }
    }

    // Display user info
    displayUserInfo();

    // Load initial tab
    showTab('giveaways-tab');
    loadStats();
}

// Global functions that need to be available immediately
window.showCreateGiveaway = function() {
    if (!isAdmin) return;
    document.getElementById('giveaway-modal').style.display = 'block';
    setTimeout(() => {
        const content = document.querySelector('#giveaway-modal .modal-content');
        if (content) {
            content.style.transform = 'scale(1)';
            content.style.opacity = '1';
        }
    }, 50);
};

window.showCreateTournament = function() {
    if (!isAdmin) return;
    document.getElementById('tournament-modal').style.display = 'block';
    setTimeout(() => {
        const content = document.querySelector('#tournament-modal .modal-content');
        if (content) {
            content.style.transform = 'scale(1)';
            content.style.opacity = '1';
        }
    }, 50);
};

window.closeModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        const content = modal.querySelector('.modal-content');
        if (content) {
            content.style.transform = 'scale(0.9)';
            content.style.opacity = '0';
        }
        setTimeout(() => {
            modal.style.display = 'none';
        }, 200);
    }
};

// Define showTab function globally and make it available immediately
window.showTab = function(tabId, event) {
    console.log('Switching to tab:', tabId);

    // Hide all content
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
        tab.classList.remove('active');
    });

    // Show selected content
    const selectedTab = document.getElementById(tabId);
    if (selectedTab) {
        selectedTab.style.display = 'block';
        selectedTab.classList.add('active');
    }

    // Update button states with animation
    document.querySelectorAll('.tab-btn').forEach(btn => {
        if (btn) {
            btn.classList.remove('active');
            btn.style.transform = 'scale(0.95)';
            setTimeout(() => {
                btn.style.transform = 'scale(1)';
            }, 100);
        }
    });

    if (event && event.target) {
        event.target.classList.add('active');
        event.target.style.transform = 'scale(1.05)';
        setTimeout(() => {
            event.target.style.transform = 'scale(1)';
        }, 200);
    } else {
        // Fallback if no event target
        const activeBtn = document.querySelector(`[onclick*="${tabId}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }
    }

    // Load content based on tab
    switch(tabId) {
        case 'giveaways-tab':
            loadGiveaways();
            break;
        case 'tournaments-tab':
            loadTournaments();
            break;
        case 'admin-tab':
            if (isAdmin) {
                showAdminPanel();
            }
            break;
        case 'stats':
            loadStats();
            break;
    }
};

// Also define as regular function for compatibility
function showTab(tabId, event) {
    return window.showTab(tabId, event);
}

// Load giveaways
async function loadGiveaways() {
    console.log('Loading giveaways...');
    try {
        const response = await fetch('/api/giveaways');
        const giveaways = await response.json();

        const container = document.getElementById('giveaways-container');
        if (!container) return;

        if (giveaways.length === 0) {
            container.innerHTML = '<div class="empty-state">Нет активных розыгрышей</div>';
            return;
        }

        container.innerHTML = giveaways.map(giveaway => `
            <div class="giveaway-card" onclick="showGiveawayDetails(${giveaway.id})">
                <h3>${giveaway.title}</h3>
                <p>${giveaway.description}</p>
                <div class="giveaway-meta">
                    <span>👥 ${giveaway.participants} участников</span>
                    <span>📅 ${new Date(giveaway.end_date).toLocaleDateString()}</span>
                </div>
                <button onclick="event.stopPropagation(); participateGiveaway(${giveaway.id}, this)" class="participate-btn">
                    Участвовать
                </button>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading giveaways:', error);
        const container = document.getElementById('giveaways-container');
        if (container) {
            container.innerHTML = '<div class="error">Ошибка загрузки</div>';
        }
    }
}

// Load tournaments
async function loadTournaments() {
    console.log('Loading tournaments...');
    try {
        const response = await fetch('/api/tournaments');
        const tournaments = await response.json();

        const container = document.getElementById('tournaments-container');
        if (!container) return;

        if (tournaments.length === 0) {
            container.innerHTML = '<div class="empty-state">Нет активных турниров</div>';
            return;
        }

        container.innerHTML = tournaments.map(tournament => `
            <div class="tournament-card" onclick="showTournamentDetails(${tournament.id})">
                <h3>${tournament.title}</h3>
                <p>${tournament.description}</p>
                <div class="tournament-meta">
                    <span>👥 ${tournament.participants} участников</span>
                    <span>📅 ${new Date(tournament.start_date).toLocaleDateString()}</span>
                </div>
                <button onclick="event.stopPropagation(); registerTournament(${tournament.id}, this)" class="register-btn">
                    Зарегистрироваться
                </button>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading tournaments:', error);
        const container = document.getElementById('tournaments-container');
        if (container) {
            container.innerHTML = '<div class="error">Ошибка загрузки</div>';
        }
    }
}

// Load stats
async function loadStats() {
    console.log('Loading stats...');
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();

        document.getElementById('total-users').textContent = stats.total_users || 0;
        document.getElementById('active-users').textContent = stats.active_users || 0;
        document.getElementById('total-giveaways').textContent = stats.total_giveaways || 0;
        document.getElementById('total-tournaments').textContent = stats.total_tournaments || 0;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Update admin UI
function updateAdminUI() {
    const adminTab = document.querySelector('[onclick*="admin"]');
    if (adminTab) {
        adminTab.style.display = isAdmin ? 'block' : 'none';
    }
}

// Show admin panel
function showAdminPanel() {
    if (!isAdmin) return;

    const adminContent = document.getElementById('admin');
    if (adminContent) {
        adminContent.innerHTML = `
            <div class="admin-panel">
                <h2>Панель администратора</h2>
                <div class="admin-actions">
                    <button onclick="showCreateGiveaway()" class="admin-btn">Создать розыгрыш</button>
                    <button onclick="showCreateTournament()" class="admin-btn">Создать турнир</button>
                </div>
            </div>
        `;
    }
}

// Show giveaway details
function showGiveawayDetails(id) {
    console.log('Showing giveaway details for ID:', id);
    if (window.Telegram && window.Telegram.WebApp) {
        window.Telegram.WebApp.showAlert(`Розыгрыш #${id} выбран`);
    }
}

// Show tournament details
function showTournamentDetails(id) {
    console.log('Showing tournament details for ID:', id);
    if (window.Telegram && window.Telegram.WebApp) {
        window.Telegram.WebApp.showAlert(`Турнир #${id} выбран`);
    }
}

// Show create giveaway form
function showCreateGiveaway() {
    if (!isAdmin) return;

    const form = `
        <div class="form-overlay" onclick="hideForm()">
            <div class="form-container" onclick="event.stopPropagation()">
                <h3>Создать розыгрыш</h3>
                <form onsubmit="submitGiveaway(event)">
                    <input type="text" name="title" placeholder="Название" required>
                    <textarea name="description" placeholder="Описание" required></textarea>
                    <input type="datetime-local" name="end_date" required>
                    <div class="form-actions">
                        <button type="button" onclick="hideForm()">Отмена</button>
                        <button type="submit">Создать</button>
                    </div>
                </form>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', form);
}

// Show create tournament form
function showCreateTournament() {
    if (!isAdmin) return;

    const form = `
        <div class="form-overlay" onclick="hideForm()">
            <div class="form-container" onclick="event.stopPropagation()">
                <h3>Создать турнир</h3>
                <form onsubmit="submitTournament(event)">
                    <input type="text" name="title" placeholder="Название" required>
                    <textarea name="description" placeholder="Описание" required></textarea>
                    <input type="datetime-local" name="start_date" required>
                    <div class="form-actions">
                        <button type="button" onclick="hideForm()">Отмена</button>
                        <button type="submit">Создать</button>
                    </div>
                </form>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', form);
}

// Hide form
function hideForm() {
    const overlay = document.querySelector('.form-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// Submit giveaway
async function submitGiveaway(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const data = {
        title: formData.get('title'),
        description: formData.get('description'),
        end_date: formData.get('end_date')
    };

    try {
        const response = await fetch('/api/giveaways', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            hideForm();
            loadGiveaways();
            if (window.Telegram && window.Telegram.WebApp) {
                window.Telegram.WebApp.showAlert('Розыгрыш создан!');
            }
        }
    } catch (error) {
        console.error('Error creating giveaway:', error);
    }
}

// Submit tournament
async function submitTournament(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const data = {
        title: formData.get('title'),
        description: formData.get('description'),
        start_date: formData.get('start_date')
    };

    try {
        const response = await fetch('/api/tournaments', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            hideForm();
            loadTournaments();
            if (window.Telegram && window.Telegram.WebApp) {
                window.Telegram.WebApp.showAlert('Турнир создан!');
            }
        }
    } catch (error) {
        console.error('Error creating tournament:', error);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, starting initialization...');
    initializeApp();
});

// Advanced animations and effects
class GameUI {
    static addGlowEffect(element) {
        element.style.boxShadow = '0 0 30px rgba(255, 107, 107, 0.6)';
        setTimeout(() => {
            element.style.boxShadow = '';
        }, 2000);
    }

    static createParticles(element) {
        const rect = element.getBoundingClientRect();
        for (let i = 0; i < 5; i++) {
            const particle = document.createElement('div');
            particle.style.cssText = `
                position: fixed;
                width: 4px;
                height: 4px;
                background: #ff6b6b;
                border-radius: 50%;
                pointer-events: none;
                z-index: 9999;
                left: ${rect.left + rect.width / 2}px;
                top: ${rect.top + rect.height / 2}px;
                animation: particle-burst 1s ease-out forwards;
            `;
            document.body.appendChild(particle);

            setTimeout(() => particle.remove(), 1000);
        }
    }

    static showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 16px 24px;
            background: ${type === 'success' ? 'rgba(76, 205, 196, 0.9)' : 'rgba(255, 107, 107, 0.9)'};
            color: white;
            border-radius: 12px;
            font-weight: 600;
            z-index: 10000;
            transform: translateX(400px);
            transition: transform 0.3s ease;
            backdrop-filter: blur(10px);
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);

        setTimeout(() => {
            notification.style.transform = 'translateX(400px)';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Add particle animation CSS
const particleCSS = document.createElement('style');
particleCSS.textContent = `
    @keyframes particle-burst {
        0% {
            opacity: 1;
            transform: scale(1) translate(0, 0);
        }
        100% {
            opacity: 0;
            transform: scale(0) translate(${Math.random() * 200 - 100}px, ${Math.random() * 200 - 100}px);
        }
    }
`;
document.head.appendChild(particleCSS);

// Enhanced modal functions
function showCreateGiveawayModal() {
    const modal = document.getElementById('giveaway-modal');
    modal.style.display = 'block';
    setTimeout(() => {
        modal.querySelector('.modal-content').style.transform = 'scale(1)';
        modal.querySelector('.modal-content').style.opacity = '1';
    }, 50);
}

function showCreateTournamentModal() {
    const modal = document.getElementById('tournament-modal');
    modal.style.display = 'block';
    setTimeout(() => {
        modal.querySelector('.modal-content').style.transform = 'scale(1)';
        modal.querySelector('.modal-content').style.opacity = '1';
    }, 50);
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.querySelector('.modal-content').style.transform = 'scale(0.9)';
    modal.querySelector('.modal-content').style.opacity = '0';
    setTimeout(() => {
        modal.style.display = 'none';
    }, 200);
}

// Enhanced tournament registration
let currentTournamentId = null;

function registerTournament(tournamentId, button) {
    if (!currentUser) {
        GameUI.showNotification('Откройте через Telegram для регистрации', 'error');
        return;
    }

    GameUI.createParticles(button);
    currentTournamentId = tournamentId;

    const modal = document.getElementById('tournament-reg-modal');
    modal.style.display = 'block';
    setTimeout(() => {
        modal.querySelector('.modal-content').style.transform = 'scale(1)';
        modal.querySelector('.modal-content').style.opacity = '1';
    }, 50);
}

async function showParticipants(tournamentId) {
    try {
        const response = await fetch(`/api/tournaments/${tournamentId}/participants`);
        const participants = await response.json();

        const container = document.getElementById('participants-container');

        if (participants.length === 0) {
            container.innerHTML = '<div class="no-content"><svg class="icon icon-lg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>Пока нет участников</div>';
        } else {
            container.innerHTML = participants.map((participant, index) => `
                <div class="participant-card" style="animation: slideInRight 0.3s ease ${index * 0.05}s both;">
                    <div class="participant-info">
                        <h4><svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="6" y1="12" x2="10" y2="12"></line><line x1="8" y1="10" x2="8" y2="14"></line><line x1="15" y1="13" x2="15.01" y2="13"></line><line x1="18" y1="11" x2="18.01" y2="11"></line><rect x="2" y="6" width="20" height="12" rx="2"></rect></svg>${participant.first_name} ${participant.username ? `(@${participant.username})` : ''}</h4>
                        <p><svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg><strong>Возраст:</strong> ${participant.age}</p>
                        <p><svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect><line x1="12" y1="18" x2="12.01" y2="18"></line></svg><strong>Телефон:</strong> ${participant.phone_brand}</p>
                        <p><svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle></svg><strong>Игровой ник:</strong> ${participant.nickname}</p>
                        <p><svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><circle cx="8" cy="9" r="2"></circle><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path><line x1="13" y1="20" x2="21" y2="20"></line><line x1="13" y1="16" x2="21" y2="16"></line></svg><strong>ID в игре:</strong> ${participant.game_id}</p>
                        <p><svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg><strong>Регистрация:</strong> ${new Date(participant.registration_date).toLocaleString()}</p>
                    </div>
                </div>
            `).join('');
        }

        const modal = document.getElementById('participants-modal');
        modal.style.display = 'block';
        setTimeout(() => {
            modal.querySelector('.modal-content').style.transform = 'scale(1)';
            modal.querySelector('.modal-content').style.opacity = '1';
        }, 50);
    } catch (error) {
        console.error('Error loading participants:', error);
        GameUI.showNotification('Ошибка загрузки участников', 'error');
    }
}

// Enhanced form submissions with better UX
document.getElementById('giveaway-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const submitBtn = this.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = '⏳ Создание...';
    submitBtn.disabled = true;

    const formData = {
        title: document.getElementById('giveaway-title').value,
        description: document.getElementById('giveaway-description').value,
        end_date: document.getElementById('giveaway-end-date').value
    };

    try {
        const response = await fetch('/api/giveaways', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            closeModal('giveaway-modal');
            GameUI.showNotification('Розыгрыш успешно создан!');
            loadGiveaways();
            this.reset();
        }
    } catch (error) {
        console.error('Error creating giveaway:', error);
        GameUI.showNotification('Ошибка создания розыгрыша', 'error');
    } finally {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
});

document.getElementById('tournament-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const submitBtn = this.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = '⏳ Создание...';
    submitBtn.disabled = true;

    const formData = {
        title: document.getElementById('tournament-title').value,
        description: document.getElementById('tournament-description').value,
        start_date: document.getElementById('tournament-start-date').value
    };

    try {
        const response = await fetch('/api/tournaments', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            closeModal('tournament-modal');
            GameUI.showNotification('Турнир успешно создан!');
            loadTournaments();
            this.reset();
        }
    } catch (error) {
        console.error('Error creating tournament:', error);
        GameUI.showNotification('Ошибка создания турнира', 'error');
    } finally {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
});

document.getElementById('tournament-reg-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const submitBtn = this.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = '⏳ Регистрация...';
    submitBtn.disabled = true;

    const formData = {
        user_id: currentUser.id,
        age: document.getElementById('user-age').value,
        phone_brand: document.getElementById('phone-brand').value,
        nickname: document.getElementById('game-nickname').value,
        game_id: document.getElementById('game-id').value
    };

    try {
        const response = await fetch(`/api/tournaments/${currentTournamentId}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (result.success) {
            closeModal('tournament-reg-modal');
            GameUI.showNotification('Вы успешно зарегистрированы на турнир!');
            loadTournaments();
            this.reset();
        } else {
            GameUI.showNotification('❌ ' + (result.error || 'Возможно, вы уже зарегистрированы'), 'error');
        }
    } catch (error) {
        console.error('Error registering for tournament:', error);
        GameUI.showNotification('Ошибка регистрации', 'error');
    } finally {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
});

async function participateGiveaway(giveawayId, button) {
    if (!currentUser) {
        GameUI.showNotification('Откройте через Telegram для участия', 'error');
        return;
    }

    GameUI.createParticles(button);

    const originalText = button.innerHTML;
    button.innerHTML = '<span>⏳ Участие...</span>';
    button.disabled = true;

    try {
        const response = await fetch(`/api/giveaways/${giveawayId}/participate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_id: currentUser.id })
        });

        const result = await response.json();

        if (result.success) {
            GameUI.showNotification('Вы участвуете в розыгрыше!');
            GameUI.addGlowEffect(button.parentElement);
            loadGiveaways();
        } else {
            GameUI.showNotification('❌ ' + (result.error || 'Возможно, вы уже участвуете'), 'error');
        }
    } catch (error) {
        console.error('Error participating in giveaway:', error);
        GameUI.showNotification('Ошибка участия в розыгрыше', 'error');
    } finally {
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

// Enhanced modal interactions
window.onclick = function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target === modal) {
            const modalContent = modal.querySelector('.modal-content');
            modalContent.style.transform = 'scale(0.9)';
            modalContent.style.opacity = '0';
            setTimeout(() => {
                modal.style.display = 'none';
            }, 200);
        }
    });
}

// Add // Global variables
let currentUser = null;
let isAdmin = false;
let isSubscribed = false;

// Define showTab function globally first
window.showTab = function(tabId, event) {
    console.log('Switching to tab:', tabId);
    
    // Hide all content
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    // Show selected content
    const selectedTab = document.getElementById(tabId);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }

    // Update button states
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    if (event && event.target) {
        event.target.classList.add('active');
    } else {
        // Fallback if no event target
        const activeBtn = document.querySelector(`[onclick*="${tabId}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }
    }
};

// CSS animations
const animationCSS = document.createElement('style');
animationCSS.textContent = `
    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    .modal-content {
        transform: scale(0.9);
        opacity: 0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
`;
document.head.appendChild(animationCSS);

function displayUserInfo() {
    const userInfoDiv = document.getElementById('user-info');
    if (currentUser) {
        userInfoDiv.innerHTML = `
            <h2><svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>Привет, ${currentUser.first_name}!</h2>
            <p>ID: ${currentUser.id}${isAdmin ? ' | ADMIN' : ''}</p>
        `;
        userInfoDiv.style.animation = 'fadeInUp 0.6s ease';
    } else {
        userInfoDiv.innerHTML = `
            <h2><svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="6" y1="12" x2="10" y2="12"></line><line x1="8" y1="10" x2="8" y2="14"></line><line x1="15" y1="13" x2="15.01" y2="13"></line><line x1="18" y1="11" x2="18.01" y2="11"></line><rect x="2" y="6" width="20" height="12" rx="2"></rect></svg>Добро пожаловать!</h2>
            <p>Откройте через Telegram для полного функционала</p>
        `;
    }
}

async function checkAdminStatus() {
    if (!currentUser) return;

    try {
        const response = await fetch('/api/check-admin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_id: currentUser.id })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        isAdmin = data.is_admin;

        if (isAdmin) {
            const adminTab = document.querySelector('.admin-only');
            if (adminTab) {
                adminTab.style.display = 'block';
                adminTab.style.animation = 'slideInRight 0.5s ease';
            }
        }
    } catch (error) {
        console.error('Error checking admin status:', error);
        isAdmin = false;
    }
}