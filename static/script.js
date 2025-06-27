// Define showTab function FIRST and make it globally available
function showTab(tabId, event) {
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

    // Update button states
    document.querySelectorAll('.tab-btn').forEach(btn => {
        if (btn) {
            btn.classList.remove('active');
        }
    });

    if (event && event.target) {
        event.target.classList.add('active');
    } else {
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
}

// Make function globally available immediately
window.showTab = showTab;

// Global variables
let currentUser = null;
let isAdmin = false;
let currentGiveawayId = null;
let currentTournamentId = null;

// Initialize Telegram WebApp
if (window.Telegram && window.Telegram.WebApp) {
    window.Telegram.WebApp.ready();
    window.Telegram.WebApp.expand();

    const tgVersion = window.Telegram.WebApp.version || '6.0';
    const majorVersion = parseFloat(tgVersion);

    if (majorVersion >= 6.1) {
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
        document.documentElement.style.setProperty('--tg-theme-bg-color', '#0a0a0f');
        document.documentElement.style.setProperty('--tg-theme-secondary-bg-color', '#1a1a2e');
    }

    currentUser = window.Telegram.WebApp.initDataUnsafe?.user;
}

// Initialize app
async function initializeApp() {
    console.log('🔧 Initializing app...');

    if (currentUser) {
        console.log('👤 User:', currentUser);
        await checkAdminStatus(currentUser.id);
        await checkSubscription(currentUser.id);
    }

    // Show default tab
    showTab('giveaways-tab');

    console.log('✅ App initialized');
}

// Check if user is admin
async function checkAdminStatus(userId) {
    try {
        const response = await fetch('/api/check-admin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        });
        const data = await response.json();
        isAdmin = data.is_admin;

        if (isAdmin) {
            document.getElementById('admin-btn').style.display = 'block';
        }
    } catch (error) {
        console.error('Error checking admin status:', error);
    }
}

// Check subscription status
async function checkSubscription(userId) {
    try {
        const response = await fetch('/api/check-subscription', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        });
        const data = await response.json();
        return data.is_subscribed;
    } catch (error) {
        console.error('Error checking subscription:', error);
        return false;
    }
}

// Load giveaways
async function loadGiveaways() {
    try {
        const response = await fetch('/api/giveaways');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const giveaways = await response.json();
        
        if (!Array.isArray(giveaways)) {
            throw new Error('Invalid giveaways data format');
        }

        const container = document.getElementById('giveaways-list');
        if (!container) {
            console.error('Giveaways container not found');
            return;
        }
        
        container.innerHTML = '';

        if (giveaways.length === 0) {
            container.innerHTML = '<div class="empty-state">🎁 Пока нет активных розыгрышей</div>';
            return;
        }

        giveaways.forEach(giveaway => {
            const giveawayEl = document.createElement('div');
            giveawayEl.className = 'giveaway-card';
            
            const adminControls = isAdmin ? `
                <div class="admin-controls">
                    <button onclick="editGiveaway(${giveaway.id})" class="admin-btn-small">✏️ Редактировать</button>
                    <button onclick="finishGiveaway(${giveaway.id})" class="admin-btn-small">🏁 Завершить</button>
                    <button onclick="deleteGiveaway(${giveaway.id})" class="admin-btn-small delete">🗑️ Удалить</button>
                    <button onclick="drawWinners(${giveaway.id})" class="admin-btn-small">🎲 Разыграть</button>
                </div>
            ` : '';
            
            giveawayEl.innerHTML = `
                <h3>${giveaway.title || 'Без названия'}</h3>
                <p>${giveaway.description || 'Без описания'}</p>
                <div class="giveaway-info">
                    <span>👥 ${giveaway.participants || 0} участников</span>
                    <span>🏆 ${giveaway.winners_count || 1} победителей</span>
                    <span>📅 ${giveaway.end_date ? new Date(giveaway.end_date).toLocaleDateString() : 'Дата не указана'}</span>
                </div>
                <button onclick="participateGiveaway(${giveaway.id})" class="participate-btn">
                    🎮 Участвовать
                </button>
                ${adminControls}
            `;
            container.appendChild(giveawayEl);
        });
    } catch (error) {
        console.error('Error loading giveaways:', error);
        const container = document.getElementById('giveaways-list');
        if (container) {
            container.innerHTML = '<div class="empty-state">❌ Ошибка загрузки розыгрышей</div>';
        }
    }
}

// Participate in giveaway
async function participateGiveaway(giveawayId) {
    if (!currentUser) {
        alert('Пользователь не найден');
        return;
    }

    const isSubscribed = await checkSubscription(currentUser.id);
    if (!isSubscribed) {
        alert('Для участия нужно подписаться на канал!');
        return;
    }

    try {
        const response = await fetch(`/api/giveaways/${giveawayId}/participate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUser.id })
        });

        const result = await response.json();
        if (result.success) {
            alert('✅ Вы успешно участвуете в розыгрыше!');
            loadGiveaways();
        } else {
            alert('❌ Вы уже участвуете в этом розыгрыше');
        }
    } catch (error) {
        console.error('Error participating:', error);
        alert('Ошибка при участии в розыгрыше');
    }
}

// Load tournaments
async function loadTournaments() {
    try {
        const response = await fetch('/api/tournaments');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const tournaments = await response.json();
        
        if (!Array.isArray(tournaments)) {
            throw new Error('Invalid tournaments data format');
        }

        const container = document.getElementById('tournaments-list');
        if (!container) {
            console.error('Tournaments container not found');
            return;
        }
        
        container.innerHTML = '';

        if (tournaments.length === 0) {
            container.innerHTML = '<div class="empty-state">🏆 Пока нет активных турниров</div>';
            return;
        }

        tournaments.forEach(tournament => {
            const tournamentEl = document.createElement('div');
            tournamentEl.className = 'tournament-card';
            
            const registrationStatus = tournament.registration_status === 'closed' ? '🔒 Регистрация закрыта' : '🏆 Регистрация';
            const registrationDisabled = tournament.registration_status === 'closed' ? 'disabled' : '';
            
            const adminControls = isAdmin ? `
                <div class="admin-controls">
                    <button onclick="toggleTournamentRegistration(${tournament.id}, '${tournament.registration_status === 'open' ? 'closed' : 'open'}')" class="admin-btn-small">
                        ${tournament.registration_status === 'open' ? '🔒 Закрыть регистрацию' : '🔓 Открыть регистрацию'}
                    </button>
                </div>
            ` : '';
            
            tournamentEl.innerHTML = `
                <h3>${tournament.title || 'Без названия'}</h3>
                <p>${tournament.description || 'Без описания'}</p>
                <div class="tournament-info">
                    <span>👥 ${tournament.participants || 0} участников</span>
                    <span>🏆 ${tournament.winners_count || 1} победителей</span>
                    <span>📅 ${tournament.start_date ? new Date(tournament.start_date).toLocaleDateString() : 'Дата не указана'}</span>
                    <span class="registration-status ${tournament.registration_status}">
                        ${tournament.registration_status === 'open' ? '🟢 Регистрация открыта' : '🔴 Регистрация закрыта'}
                    </span>
                </div>
                <button onclick="showTournamentRegistration(${tournament.id})" class="register-btn" ${registrationDisabled}>
                    ${registrationStatus}
                </button>
                ${adminControls}
            `;
            container.appendChild(tournamentEl);
        });
    } catch (error) {
        console.error('Error loading tournaments:', error);
        const container = document.getElementById('tournaments-list');
        if (container) {
            container.innerHTML = '<div class="empty-state">❌ Ошибка загрузки турниров</div>';
        }
    }
}

// Show tournament registration form
function showTournamentRegistration(tournamentId) {
    currentTournamentId = tournamentId;
    const modal = document.getElementById('tournament-registration');
    if (modal) {
        modal.style.display = 'block';
        // Clear form
        const form = modal.querySelector('form');
        if (form) form.reset();
    } else {
        console.error('Tournament registration modal not found');
    }
}

// Register for tournament
async function registerTournament() {
    if (!currentUser || !currentTournamentId) return;

    const isSubscribed = await checkSubscription(currentUser.id);
    if (!isSubscribed) {
        alert('Для участия нужно подписаться на канал!');
        return;
    }

    const formData = {
        user_id: currentUser.id,
        age: document.getElementById('age').value,
        phone_brand: document.getElementById('phone-brand').value,
        nickname: document.getElementById('nickname').value,
        game_id: document.getElementById('game-id').value
    };

    try {
        const response = await fetch(`/api/tournaments/${currentTournamentId}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        const result = await response.json();
        if (result.success) {
            alert('✅ Вы успешно зарегистрированы на турнир!');
            document.getElementById('tournament-registration').style.display = 'none';
            loadTournaments();
        } else {
            alert('❌ Вы уже зарегистрированы на этот турнир');
        }
    } catch (error) {
        console.error('Error registering for tournament:', error);
        alert('Ошибка при регистрации на турнир');
    }
}

// Show admin panel
function showAdminPanel() {
    if (!isAdmin) return;

    document.getElementById('admin-content').innerHTML = `
        <div class="admin-panel">
            <h2>🔧 Панель администратора</h2>
            <div class="admin-buttons">
                <button onclick="showCreateGiveaway()" class="admin-btn">🎁 Создать розыгрыш</button>
                <button onclick="showCreateTournament()" class="admin-btn">🏆 Создать турнир</button>
                <button onclick="loadStats()" class="admin-btn">📊 Статистика</button>
            </div>
        </div>
    `;
}

// Show create giveaway form
function showCreateGiveaway() {
    document.getElementById('admin-content').innerHTML = `
        <div class="create-form">
            <h2>🎁 Создать розыгрыш</h2>
            <input type="text" id="giveaway-title" placeholder="Название розыгрыша" />
            <textarea id="giveaway-description" placeholder="Описание розыгрыша"></textarea>
            <input type="datetime-local" id="giveaway-end-date" />
            <input type="number" id="giveaway-winners" placeholder="Количество победителей" min="1" value="1" />
            <button onclick="createGiveaway()" class="create-btn">Создать</button>
            <button onclick="showAdminPanel()" class="cancel-btn">Отмена</button>
        </div>
    `;
}

// Create giveaway
async function createGiveaway() {
    const data = {
        title: document.getElementById('giveaway-title').value,
        description: document.getElementById('giveaway-description').value,
        end_date: document.getElementById('giveaway-end-date').value,
        winners_count: parseInt(document.getElementById('giveaway-winners').value) || 1
    };

    try {
        const response = await fetch('/api/giveaways', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (result.success) {
            alert('✅ Розыгрыш создан!');
            showAdminPanel();
            loadGiveaways();
        }
    } catch (error) {
        console.error('Error creating giveaway:', error);
        alert('Ошибка при создании розыгрыша');
    }
}

// Show create tournament form
function showCreateTournament() {
    document.getElementById('admin-content').innerHTML = `
        <div class="create-form">
            <h2>🏆 Создать турнир</h2>
            <input type="text" id="tournament-title" placeholder="Название турнира" />
            <textarea id="tournament-description" placeholder="Описание турнира"></textarea>
            <input type="datetime-local" id="tournament-start-date" />
            <input type="number" id="tournament-winners" placeholder="Количество победителей" min="1" value="1" />
            <button onclick="createTournament()" class="create-btn">Создать</button>
            <button onclick="showAdminPanel()" class="cancel-btn">Отмена</button>
        </div>
    `;
}

// Create tournament
async function createTournament() {
    const data = {
        title: document.getElementById('tournament-title').value,
        description: document.getElementById('tournament-description').value,
        start_date: document.getElementById('tournament-start-date').value,
        winners_count: parseInt(document.getElementById('tournament-winners').value) || 1
    };

    try {
        const response = await fetch('/api/tournaments', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (result.success) {
            alert('✅ Турнир создан!');
            showAdminPanel();
            loadTournaments();
        }
    } catch (error) {
        console.error('Error creating tournament:', error);
        alert('Ошибка при создании турнира');
    }
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const stats = await response.json();
        
        // Check if we're in admin tab or stats tab
        const statsContent = document.getElementById('stats-content');
        const adminContent = document.getElementById('admin-content');
        
        const statsHTML = `
            <div class="stats-panel">
                <h2>📊 Статистика сервиса</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>👥 Всего пользователей</h3>
                        <span class="stat-number">${stats.total_users || 0}</span>
                    </div>
                    <div class="stat-card">
                        <h3>✅ Активных пользователей</h3>
                        <span class="stat-number">${stats.active_users || 0}</span>
                    </div>
                    <div class="stat-card">
                        <h3>🎁 Всего розыгрышей</h3>
                        <span class="stat-number">${stats.total_giveaways || 0}</span>
                    </div>
                    <div class="stat-card">
                        <h3>🏆 Всего турниров</h3>
                        <span class="stat-number">${stats.total_tournaments || 0}</span>
                    </div>
                </div>
                ${isAdmin ? '<button onclick="showAdminPanel()" class="back-btn">Назад к админке</button>' : ''}
            </div>
        `;
        
        if (statsContent) {
            statsContent.innerHTML = statsHTML;
        }
        
        if (adminContent && isAdmin) {
            adminContent.innerHTML = statsHTML;
        }
        
    } catch (error) {
        console.error('Error loading stats:', error);
        const errorHTML = '<div class="empty-state">❌ Ошибка загрузки статистики</div>';
        
        const statsContent = document.getElementById('stats-content');
        const adminContent = document.getElementById('admin-content');
        
        if (statsContent) {
            statsContent.innerHTML = errorHTML;
        }
        
        if (adminContent && isAdmin) {
            adminContent.innerHTML = errorHTML;
        }
    }
}

// Cancel tournament registration
function cancelTournamentRegistration() {
    const modal = document.getElementById('tournament-registration');
    if (modal) {
        modal.style.display = 'none';
        currentTournamentId = null;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeApp);

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

// Window load event
window.addEventListener('load', function() {
    console.log('✅ Page loaded, initializing...');
    initializeApp();
});

// Admin functions for giveaway management
async function editGiveaway(giveawayId) {
    // Get current giveaway data
    try {
        const response = await fetch('/api/giveaways');
        const giveaways = await response.json();
        const giveaway = giveaways.find(g => g.id === giveawayId);
        
        if (!giveaway) {
            alert('Розыгрыш не найден');
            return;
        }
        
        document.getElementById('admin-content').innerHTML = `
            <div class="create-form">
                <h2>✏️ Редактировать розыгрыш</h2>
                <input type="text" id="edit-giveaway-title" value="${giveaway.title}" />
                <textarea id="edit-giveaway-description">${giveaway.description}</textarea>
                <input type="datetime-local" id="edit-giveaway-end-date" value="${giveaway.end_date ? giveaway.end_date.slice(0, 16) : ''}" />
                <input type="number" id="edit-giveaway-winners" value="${giveaway.winners_count || 1}" min="1" />
                <button onclick="updateGiveaway(${giveawayId})" class="create-btn">Сохранить</button>
                <button onclick="showAdminPanel()" class="cancel-btn">Отмена</button>
            </div>
        `;
    } catch (error) {
        console.error('Error loading giveaway:', error);
        alert('Ошибка загрузки данных розыгрыша');
    }
}

async function updateGiveaway(giveawayId) {
    const data = {
        title: document.getElementById('edit-giveaway-title').value,
        description: document.getElementById('edit-giveaway-description').value,
        end_date: document.getElementById('edit-giveaway-end-date').value,
        winners_count: parseInt(document.getElementById('edit-giveaway-winners').value) || 1
    };

    try {
        const response = await fetch(`/api/giveaways/${giveawayId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (result.success) {
            alert('✅ Розыгрыш обновлен!');
            showAdminPanel();
            loadGiveaways();
        }
    } catch (error) {
        console.error('Error updating giveaway:', error);
        alert('Ошибка при обновлении розыгрыша');
    }
}

async function finishGiveaway(giveawayId) {
    if (!confirm('Завершить розыгрыш? Это действие нельзя отменить.')) return;

    try {
        const response = await fetch(`/api/giveaways/${giveawayId}/finish`, {
            method: 'POST'
        });

        const result = await response.json();
        if (result.success) {
            alert('✅ Розыгрыш завершен!');
            loadGiveaways();
        }
    } catch (error) {
        console.error('Error finishing giveaway:', error);
        alert('Ошибка при завершении розыгрыша');
    }
}

async function deleteGiveaway(giveawayId) {
    if (!confirm('Удалить розыгрыш? Это действие нельзя отменить!')) return;

    try {
        const response = await fetch(`/api/giveaways/${giveawayId}`, {
            method: 'DELETE'
        });

        const result = await response.json();
        if (result.success) {
            alert('✅ Розыгрыш удален!');
            loadGiveaways();
        }
    } catch (error) {
        console.error('Error deleting giveaway:', error);
        alert('Ошибка при удалении розыгрыша');
    }
}

async function drawWinners(giveawayId) {
    if (!confirm('Провести розыгрыш победителей?')) return;

    try {
        const response = await fetch(`/api/giveaways/${giveawayId}/draw`, {
            method: 'POST'
        });

        const result = await response.json();
        if (result.success) {
            alert(`🎉 Победитель: ${result.winner.name} (@${result.winner.username || 'без username'})`);
        } else {
            alert('❌ ' + (result.error || 'Ошибка при проведении розыгрыша'));
        }
    } catch (error) {
        console.error('Error drawing winner:', error);
        alert('Ошибка при проведении розыгрыша');
    }
}

async function toggleTournamentRegistration(tournamentId, newStatus) {
    try {
        const response = await fetch(`/api/tournaments/${tournamentId}/toggle-registration`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });

        const result = await response.json();
        if (result.success) {
            const statusText = newStatus === 'open' ? 'открыта' : 'закрыта';
            alert(`✅ Регистрация ${statusText}!`);
            loadTournaments();
        }
    } catch (error) {
        console.error('Error toggling registration:', error);
        alert('Ошибка при изменении статуса регистрации');
    }
}

console.log('🚀 Script.js loaded successfully');