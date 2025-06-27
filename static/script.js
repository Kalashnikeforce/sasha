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

    // Проверяем URL параметры для турнира
    const urlParams = new URLSearchParams(window.location.search);
    const tournamentId = urlParams.get('tournament');

    if (tournamentId) {
        console.log('🏆 Tournament ID found:', tournamentId);
        // Переключаемся на вкладку турниров и открываем форму регистрации
        showTab('tournaments-tab');
        // Небольшая задержка чтобы турниры загрузились
        setTimeout(() => {
            showTournamentRegistration(parseInt(tournamentId));
        }, 1000);
    } else {
        // Show default tab
        showTab('giveaways-tab');
    }

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

            const currentStatus = tournament.registration_status || 'open';
            const registrationStatus = currentStatus === 'closed' ? '🔒 Регистрация закрыта' : '🏆 Регистрация';
            const registrationDisabled = currentStatus === 'closed' ? 'disabled' : '';

            const adminControls = isAdmin ? `
                <div class="admin-controls">
                    <button onclick="toggleTournamentRegistration(${tournament.id})" class="admin-btn-small">
                        ${currentStatus === 'closed' ? '🔓 Открыть регистрацию' : '🔒 Закрыть регистрацию'}
                    </button>
                    <button onclick="deleteTournament(${tournament.id})" class="admin-btn-small delete">🗑️ Удалить</button>
                </div>
            ` : '';

            tournamentEl.innerHTML = `
                <h3>${tournament.title || 'Без названия'}</h3>
                <p>${tournament.description || 'Без описания'}</p>
                <div class="tournament-info">
                    <span>👥 ${tournament.participants || 0} участников</span>
                    <span>🏆 ${tournament.winners_count || 1} победителей</span>
                    <span>📅 ${tournament.start_date ? new Date(tournament.start_date).toLocaleDateString() : 'Дата не указана'}</span>
                </div>
                <div class="tournament-registration-block">
                    <div class="registration-status-block ${currentStatus}">
                        ${currentStatus === 'closed' ? '🔒 Регистрация закрыта' : '✅ Регистрация открыта'}
                    </div>
                    <button onclick="showTournamentRegistration(${tournament.id})" class="register-btn" ${registrationDisabled}>
                        ${registrationStatus}
                    </button>
                </div>
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
async function showTournamentRegistration(tournamentId) {
    // Проверяем статус турнира перед открытием формы
    try {
        const response = await fetch('/api/tournaments');
        const tournaments = await response.json();
        const tournament = tournaments.find(t => t.id === tournamentId);

        if (tournament && tournament.registration_status === 'closed') {
            alert('❌ Регистрация на этот турнир закрыта!');
            return;
        }
    } catch (error) {
        console.error('Error checking tournament status:', error);
    }

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
            <div class="admin-grid">
                <div class="admin-card" onclick="showCreateGiveaway()">
                    <div class="admin-card-icon">🎁</div>
                    <h3>Создать розыгрыш</h3>
                    <p>Создание нового розыгрыша с настройкой призов</p>
                </div>
                <div class="admin-card" onclick="showCreateTournament()">
                    <div class="admin-card-icon">🏆</div>
                    <h3>Создать турнир</h3>
                    <p>Создание турнира с настройкой призовых мест</p>
                </div>
                <div class="admin-card" onclick="loadAdminStats()">
                    <div class="admin-card-icon">📊</div>
                    <h3>Статистика</h3>
                    <p>Просмотр статистики пользователей и активности</p>
                </div>
            </div>
        </div>
    `;
}

// Show create giveaway form
function showCreateGiveaway() {
    document.getElementById('admin-content').innerHTML = `
        <div class="create-form">
            <h2>🎁 Создать розыгрыш</h2>
            <div class="form-group">
                <label>Название розыгрыша</label>
                <input type="text" id="giveaway-title" placeholder="Введите название" />
            </div>
            <div class="form-group">
                <label>Описание</label>
                <textarea id="giveaway-description" placeholder="Описание розыгрыша" rows="4"></textarea>
            </div>
            <div class="form-group">
                <label>Дата окончания</label>
                <input type="datetime-local" id="giveaway-end-date" />
            </div>
            <div class="form-group">
                <label>Количество победителей</label>
                <input type="number" id="giveaway-winners" placeholder="1" min="1" max="10" value="1" onchange="updatePrizePlaces('giveaway')" />
            </div>
            <div id="giveaway-prizes" class="prizes-section">
                <div class="form-group">
                    <label>🥇 Приз за 1 место</label>
                    <input type="text" id="prize-1" placeholder="Что получает победитель" />
                </div>
            </div>
            <div class="form-buttons">
                <button onclick="createGiveaway()" class="create-btn">Создать розыгрыш</button>
                <button onclick="showAdminPanel()" class="cancel-btn">Отмена</button>
            </div>
        </div>
    `;
}

// Create giveaway
async function createGiveaway() {
    const title = document.getElementById('giveaway-title').value;
    const description = document.getElementById('giveaway-description').value;
    const endDate = document.getElementById('giveaway-end-date').value;
    const winnersCount = parseInt(document.getElementById('giveaway-winners').value) || 1;

    if (!title || !description || !endDate) {
        alert('Пожалуйста, заполните все поля');
        return;
    }

    // Собираем призы
    const prizes = [];
    for (let i = 1; i <= winnersCount; i++) {
        const prizeInput = document.getElementById(`prize-${i}`);
        if (prizeInput && prizeInput.value.trim()) {
            prizes.push(prizeInput.value.trim());
        }
    }

    try {
        const response = await fetch('/api/giveaways', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title,
                description,
                end_date: endDate,
                winners_count: winnersCount,
                prizes: prizes
            })
        });

        const result = await response.json();
        if (result.success) {
            alert('Розыгрыш создан успешно!');
            closeModal('create-giveaway-modal');
            loadGiveaways();
        } else {
            alert('Ошибка: ' + (result.error || 'Неизвестная ошибка'));
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
            <div class="form-group">
                <label>Название турнира</label>
                <input type="text" id="tournament-title" placeholder="Введите название" />
            </div>
            <div class="form-group">
                <label>Описание</label>
                <textarea id="tournament-description" placeholder="Описание турнира" rows="4"></textarea>
            </div>
            <div class="form-group">
                <label>Дата начала</label>
                <input type="datetime-local" id="tournament-start-date" />
            </div>
            <div class="form-group">
                <label>Количество победителей</label>
                <input type="number" id="tournament-winners" placeholder="1" min="1" max="10" value="1" onchange="updatePrizePlaces('tournament')" />
            </div>
            <div id="tournament-prizes" class="prizes-section">
                <div class="form-group">
                    <label>🥇 Приз за 1 место</label>
                    <input type="text" id="tournament-prize-1" placeholder="Что получает победитель" />
                </div>
            </div>
            <div class="form-buttons">
                <button onclick="createTournament()" class="create-btn">Создать турнир</button>
                <button onclick="showAdminPanel()" class="cancel-btn">Отмена</button>
            </div>
        </div>
    `;
}

// Create tournament
async function createTournament() {
    const title = document.getElementById('tournament-title').value;
    const description = document.getElementById('tournament-description').value;
    const startDate = document.getElementById('tournament-start-date').value;
    const winnersCount = parseInt(document.getElementById('tournament-winners').value) || 1;

    if (!title || !description || !startDate) {
        alert('Пожалуйста, заполните все поля');
        return;
    }

    // Собираем призы
    const prizes = [];
    for (let i = 1; i <= winnersCount; i++) {
        const prizeInput = document.getElementById(`tournament-prize-${i}`);
        if (prizeInput && prizeInput.value.trim()) {
            prizes.push(prizeInput.value.trim());
        }
    }

    const data = {
        title,
        description,
        start_date: startDate,
        winners_count: winnersCount,
        prizes: prizes
    };

    try {
        const response = await fetch('/api/tournaments', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (result.success) {
             // Reload tournaments after creation.
            alert('✅ Турнир создан и опубликован в канале!');
            showAdminPanel();
            loadTournaments();
        } else {
            alert('Ошибка: ' + (result.error || 'Неизвестная ошибка'));
        }
    } catch (error) {
        console.error('Error creating tournament:', error);
        alert('Ошибка при создании турнира');
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

        // Format date for datetime-local input
        let formattedDate = '';
        if (giveaway.end_date) {
            const datee = new Date(giveaway.end_date);
            formattedDate = date.toISOString().slice(0, 16);
        }

        document.getElementById('admin-content').innerHTML = `
            <div class="create-form">
                <h2>✏️ Редактировать розыгрыш</h2>
                <div class="form-group">
                    <label>Название розыгрыша</label>
                    <input type="text" id="edit-giveaway-title" value="${giveaway.title || ''}" placeholder="Введите название" />
                </div>
                <div class="form-group">
                    <label>Описание</label>
                    <textarea id="edit-giveaway-description" placeholder="Описание розыгрыша" rows="4">${giveaway.description || ''}</textarea>
                </div>
                <div class="form-group">
                    <label>Дата окончания</label>
                    <input type="datetime-local" id="edit-giveaway-end-date" value="${formattedDate}" />
                </div>
                <div class="form-group">
                    <label>Количество победителей</label>
                    <input type="number" id="edit-giveaway-winners" value="${giveaway.winners_count || 1}" min="1" max="10" />
                </div>
                <div class="form-buttons">
                    <button onclick="updateGiveaway(${giveawayId})" class="create-btn">Сохранить изменения</button>
                    <button onclick="showAdminPanel()" class="cancel-btn">Отмена</button>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading giveaway:', error);
        alert('Ошибка загрузки данных розыгрыша');
    }
}

async function updateGiveaway(giveawayId) {
    const titleEl = document.getElementById('edit-giveaway-title');
    const descriptionEl = document.getElementById('edit-giveaway-description');
    const endDateEl = document.getElementById('edit-giveaway-end-date');
    const winnersEl = document.getElementById('edit-giveaway-winners');

    if (!titleEl || !descriptionEl || !endDateEl || !winnersEl) {
        alert('❌ Ошибка: не все поля формы найдены');
        return;
    }

    if (!titleEl.value.trim()) {
        alert('❌ Название розыгрыша не может быть пустым');
        return;
    }

    const data = {
        title: titleEl.value.trim(),
        description: descriptionEl.value.trim(),
        end_date: endDateEl.value,
        winners_count: parseInt(winnersEl.value) || 1
    };

    try {
        const response = await fetch(`/api/giveaways/${giveawayId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        if (result.success) {
            alert('✅ Розыгрыш успешно обновлен!');
            showAdminPanel();
            await loadGiveaways();
        } else {
            alert('❌ Ошибка при обновлении розыгрыша');
        }
    } catch (error) {
        console.error('Error updating giveaway:', error);
        alert('❌ Ошибка при обновлении розыгрыша: ' + error.message);
    }
}

async function finishGiveaway(giveawayId) {
    if (!confirm('🏁 Завершить розыгрыш без выбора победителей?\n\n⚠️ Это действие нельзя отменить. Используйте эту кнопку только если хотите закрыть розыгрыш досрочно.')) return;

    try {
        const response = await fetch(`/api/giveaways/${giveawayId}/finish`, {
            method: 'POST'
        });

        const result = await response.json();
        if (result.success) {
            alert('✅ Розыгрыш завершен досрочно!');
            loadGiveaways();
        }
    } catch (error) {
        console.error('Error finishing giveaway:', error);
        alert('❌ Ошибка при завершении розыгрыша');
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
    if (!confirm('🎲 Провести честный розыгрыш и выбрать победителей?\n\n⚠️ После этого розыгрыш будет автоматически завершен и уведомления отправлены всем участникам!')) return;

    try {
        const response = await fetch(`/api/giveaways/${giveawayId}/draw`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            if (result.winner) {
                alert(`🎉 ${result.message}\n\n👤 ${result.winner.name} (@${result.winner.username || 'без username'})\n\n✅ Розыгрыш завершен!\n📤 Уведомления отправлены всем участникам!`);
            } else if (result.winners) {
                let winnersText = result.winners.map((winner, index) => 
                    `${index + 1}. ${winner.name} (@${winner.username || 'без username'})`
                ).join('\n');

                alert(`🎉 ${result.message}\n\n🏆 Победители:\n${winnersText}\n\n✅ Розыгрыш завершен!\n📤 Уведомления отправлены всем участникам!`);
            }

            await loadGiveaways();
        } else {
            alert('❌ ' + (result.error || 'Ошибка при проведении розыгрыша'));
        }
    } catch (error) {
        console.error('Error drawing winner:', error);
        alert('❌ Ошибка при проведении розыгрыша');
    }
}

async function toggleTournamentRegistration(tournamentId) {
    try {
        const response = await fetch('/api/tournaments');
        const tournaments = await response.json();
        const tournament = tournaments.find(t => t.id === tournamentId);

        if (!tournament) {
            alert('Турнир не найден');
            return;
        }

        const currentStatus = tournament.registration_status || 'open';
        const newStatus = currentStatus === 'open' ? 'closed' : 'open';

        const toggleResponse = await fetch(`/api/tournaments/${tournamentId}/toggle-registration`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: newStatus })
        });

        const result = await toggleResponse.json();

        if (result.success) {
            alert(`✅ Статус регистрации изменен на: ${newStatus === 'open' ? 'Открыта' : 'Закрыта'}`);
            loadTournaments(); // Перезагружаем список турниров
        } else {
            alert('❌ Ошибка при изменении статуса: ' + (result.error || 'Неизвестная ошибка'));
        }
    } catch (error) {
        console.error('Error toggling tournament registration:', error);
        alert('❌ Ошибка при изменении статуса регистрации');
    }
}

async function deleteTournament(tournamentId) {
    if (!confirm('Удалить турнир? Это действие нельзя отменить!\n\nВсе участники и данные турнира будут удалены.')) return;

    try {
        const response = await fetch(`/api/tournaments/${tournamentId}`, {
            method: 'DELETE'
        });

        const result = await response.json();
        if (result.success) {
            alert('✅ Турнир удален!');
            loadTournaments();
        } else {
            alert('❌ Ошибка: ' + (result.error || 'Не удалось удалить турнир'));
        }
    } catch (error) {
        console.error('Error deleting tournament:', error);
        alert('Ошибка при удалении турнира');
    }
}

// Update prize places based on winners count
function updatePrizePlaces(type) {
    const winnersInput = document.getElementById(`${type}-winners`);
    const prizesContainer = document.getElementById(`${type}-prizes`);
    const count = parseInt(winnersInput.value) || 1;

    const medals = ['🥇', '🥈', '🥉'];
    const places = ['1 место', '2 место', '3 место'];

    let html = '';
    for (let i = 1; i <= Math.min(count, 10); i++) {
        const medal = i <= 3 ? medals[i-1] : '🏆';
        const place = i <= 3 ? places[i-1] : `${i} место`;
        const prefix = type === 'tournament' ? 'tournament-' : '';

        html += `
            <div class="form-group">
                <label>${medal} Приз за ${place}</label>
                <input type="text" id="${prefix}prize-${i}" placeholder="Что получает за ${place}" />
            </div>
        `;
    }

    prizesContainer.innerHTML = html;
}

// Load admin stats
async function loadAdminStats() {
    try {
        const response = await fetch('/api/stats');

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const stats = await response.json();

        document.getElementById('admin-content').innerHTML = `
            <div class="admin-stats">
                <div class="stats-header">
                    <h2>📊 Статистика сервиса</h2>
                    <button onclick="showAdminPanel()" class="back-btn">← Назад</button>
                </div>
                <div class="compact-stats-grid">
                    <div class="compact-stat-card">
                        <div class="stat-icon">👥</div>
                        <div class="stat-info">
                            <div class="stat-number">${stats.total_users || 0}</div>
                            <div class="stat-label">Всего пользователей</div>
                        </div>
                    </div>
                    <div class="compact-stat-card">
                        <div class="stat-icon">✅</div>
                        <div class="stat-info">
                            <div class="stat-number">${stats.active_users || 0}</div>
                            <div class="stat-label">Активных пользователей</div>
                        </div>
                    </div>
                    <div class="compact-stat-card">
                        <div class="stat-icon">🎁</div>
                        <div class="stat-info">
                            <div class="stat-number">${stats.total_giveaways || 0}</div>
                            <div class="stat-label">Всего розыгрышей</div>
                        </div>
                    </div>
                    <div class="compact-stat-card">
                        <div class="stat-icon">🏆</div>
                        <div class="stat-info">
                            <div class="stat-number">${stats.total_tournaments || 0}</div>
                            <div class="stat-label">Всего турниров</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

    } catch (error) {
        console.error('Error loading admin stats:', error);
        document.getElementById('admin-content').innerHTML = `
            <div class="admin-stats">
                <div class="stats-header">
                    <h2>📊 Статистика</h2>
                    <button onclick="showAdminPanel()" class="back-btn">← Назад</button>
                </div>
                <div class="error-message">❌ Ошибка загрузки статистики</div>
            </div>
        `;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeApp);

// Window load event
window.addEventListener('load', function() {
    console.log('✅ Page loaded, initializing...');
    initializeApp();
});

console.log('🚀 Script.js loaded successfully');