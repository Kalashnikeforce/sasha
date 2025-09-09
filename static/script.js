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
function initTelegramWebApp() {
    console.log('🚀 Initializing Telegram WebApp...');

    if (window.Telegram?.WebApp) {
        const tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();

        const user = tg.initDataUnsafe?.user;
        if (user) {
            console.log('✅ Telegram user data:', user);
            console.log('👤 User ID:', user.id);
            currentUser = user;
            checkAdminStatus(user.id);
            checkSubscription(user.id);
        } else {
            console.log('❌ No Telegram user data available');
            // Для разработки используем тестовый ID админа
            console.log('🔧 Using test admin ID for development');
            currentUser = { id: 7541656937, first_name: 'Test Admin' };
            checkAdminStatus(7541656937); // Первый ID из конфига
        }
    } else {
        console.log('❌ Telegram WebApp not available - using test data');
        // Test data for development - используем реальный admin ID
        currentUser = { id: 7541656937, first_name: 'Test Admin' };
        checkAdminStatus(7541656937); // Первый ID из конфига
        checkSubscription(7541656937);
    }
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
        console.log('🔐 Checking admin status for user:', userId);

        const response = await fetch('/api/check-admin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        });

        const data = await response.json();
        console.log('📋 Server response:', data);

        // ВАЖНО: Сохраняем результат в глобальную переменную
        isAdmin = data.is_admin === true;
        console.log('✅ Admin check result:', isAdmin);

        const adminBtn = document.getElementById('admin-btn');
        const adminTab = document.getElementById('admin-tab');

        if (isAdmin) {
            if (adminBtn) {
                adminBtn.style.display = 'block';
                console.log('✅ Admin button activated for user:', userId);
            }

            if (adminTab) {
                adminTab.style.display = 'block';
                console.log('✅ Admin tab activated for user:', userId);
            }
        } else {
            console.log('❌ User is not admin:', userId);
        }
    } catch (error) {
        console.error('❌ Error checking admin status:', error);

        // В случае ошибки в PREVIEW режиме - даем админку всем
        if (window.location.hostname.includes('repl.co') || window.location.hostname.includes('replit')) {
            console.log('🔧 PREVIEW MODE: Granting admin access due to environment');
            isAdmin = true;
            const adminBtn = document.getElementById('admin-btn');
            const adminTab = document.getElementById('admin-tab');

            if (adminBtn) adminBtn.style.display = 'block';
            if (adminTab) adminTab.style.display = 'block';
        }
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

            const formattedDate = giveaway.end_date ? new Date(giveaway.end_date).toLocaleDateString('ru-RU') : 'Дата не указана';

            let giveawayHTML = `
                <h3>${giveaway.title || 'Без названия'}</h3>
                <p>${giveaway.description || 'Без описания'}</p>
            `;

            giveawayHTML += `
                <div class="giveaway-meta">
                    <span>🏆 Призов: ${giveaway.winners_count || 1}</span>
                    <span class="participants-count">👥 ${giveaway.participants || 0}</span>
                    <span>📅 ${formattedDate}</span>
                    <span class="status ${giveaway.status || 'active'}">${giveaway.status === 'completed' ? '✅ Завершен' : '⏳ Активен'}</span>
                </div>
                <div class="giveaway-actions">
                    ${giveaway.status !== 'completed' ? `
                        <button onclick="participateGiveaway(${giveaway.id})" class="participate-btn">
                            🎮 Участвовать
                        </button>
                    ` : ''}
                    ${isAdmin ? `
                        <div class="admin-controls">
                            ${giveaway.status !== 'completed' ? `
                                <button onclick="drawWinners(${giveaway.id})" class="admin-btn-small draw-btn" title="Провести розыгрыш">
                                    🎲 Розыгрыш
                                </button>
                            ` : ''}
                            <button onclick="deleteGiveaway(${giveaway.id})" class="admin-btn-small delete-btn" title="Удалить розыгрыш">
                                🗑️ Удалить
                            </button>
                        </div>
                    ` : ''}
                </div>
            </div>
            `;
            giveawayEl.innerHTML = giveawayHTML;
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
    console.log('🎮 Attempting to participate in giveaway:', giveawayId);

    if (!currentUser) {
        alert('❌ Пользователь не найден');
        return;
    }

    console.log('👤 Current user:', currentUser);

    try {
        // Проверяем подписку
        const isSubscribed = await checkSubscription(currentUser.id);
        if (!isSubscribed) {
            alert('❌ Для участия нужно подписаться на канал!');
            return;
        }

        console.log('✅ User is subscribed, sending participation request...');

        const response = await fetch(`/api/giveaways/${giveawayId}/participate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ user_id: currentUser.id })
        });

        console.log('📡 Response status:', response.status);
        console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()));

        if (!response.ok) {
            const errorText = await response.text();
            console.error('❌ Server error response:', errorText);
            throw new Error(`Server error: ${response.status} - ${errorText}`);
        }

        const result = await response.json();
        console.log('📋 Server response:', result);

        if (result.success) {
            alert('✅ Вы успешно участвуете в розыгрыше!');
            await loadGiveaways(); // Обновляем список
        } else {
            alert('❌ ' + (result.error || 'Вы уже участвуете в этом розыгрыше'));
        }
    } catch (error) {
        console.error('❌ Error participating in giveaway:', error);
        alert('❌ Ошибка при участии в розыгрыше: ' + error.message);
    }
}

// Load tournaments
async function loadTournaments() {
    try {
        const response = await fetch('/api/tournaments');
        const tournaments = await response.json();
        const container = document.getElementById('tournaments-list');

        if (!tournaments || tournaments.length === 0) {
            container.innerHTML = '<div class="empty-state">📝 Нет активных турниров</div>';
            return;
        }

        // Фильтруем турниры для обычных пользователей - показываем только с открытой регистрацией
        const visibleTournaments = isAdmin ? tournaments : tournaments.filter(t => {
            const status = t.registration_status || 'open';
            return status === 'open';
        });

        if (visibleTournaments.length === 0) {
            container.innerHTML = '<div class="empty-state">📝 Нет доступных турниров</div>';
            return;
        }

        container.innerHTML = ''; // Очищаем контейнер

        visibleTournaments.forEach(tournament => {
            const tournamentEl = document.createElement('div');
            tournamentEl.className = 'tournament-card';
            tournamentEl.setAttribute('data-tournament-id', tournament.id);

            const status = tournament.registration_status || 'open';
            const isClosed = status === 'closed';

            const formattedDate = tournament.start_date ? new Date(tournament.start_date).toLocaleDateString('ru-RU') : 'TBA';

            let tournamentHTML = `
                <h3>${tournament.title || 'Без названия'}</h3>
                <p>${tournament.description || 'Без описания'}</p>
            `;

            tournamentHTML += `
                <div class="tournament-meta">
                    <span>🏆 Призов: ${tournament.winners_count || 1}</span>
                    <span class="participants-count">👥 ${tournament.participants || 0}</span>
                    <span>🚀 ${formattedDate}</span>
                    <span class="status ${status}">${status === 'closed' ? '🔒 Закрыт' : '🔓 Открыт'}</span>
                </div>
                <div class="tournament-actions">
                    ${status !== 'closed' ? `
                        <button onclick="showTournamentRegistration(${tournament.id})" class="participate-btn">
                            🏆 Регистрация
                        </button>
                    ` : ''}
                    ${isAdmin ? `
                        <div class="admin-controls">
                            <button onclick="toggleTournamentRegistration(${tournament.id}, '${status}')" class="admin-btn-small toggle-btn">
                                ${status === 'open' ? '🔒 Закрыть' : '🔓 Открыть'}
                            </button>
                            <button onclick="deleteTournament(${tournament.id})" class="admin-btn-small delete-btn" title="Удалить турнир">
                                🗑️ Удалить
                            </button>
                        </div>
                    ` : ''}
                </div>
            </div>
            `;
            tournamentEl.innerHTML = tournamentHTML;
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
    console.log(`🏆 Attempting to show registration for tournament ${tournamentId}`);

    if (!currentUser) {
        alert('❌ Пользователь не найден');
        return;
    }

    // Проверяем подписку
    const isSubscribed = await checkSubscription(currentUser.id);
    if (!isSubscribed) {
        alert('❌ Для участия нужно подписаться на канал!');
        return;
    }

    // Fetch tournament details to check registration status
    try {
        const response = await fetch(`/api/tournaments/${tournamentId}`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const tournament = await response.json();
        console.log('🏆 Tournament data:', tournament);

        if (tournament.error) {
            alert('❌ Турнир не найден!');
            return;
        }

        const registrationStatus = tournament.registration_status || tournament.status || 'open';
        if (registrationStatus === 'closed') {
            alert('❌ Регистрация на турнир закрыта!');
            return;
        }

        console.log('✅ Tournament registration is open');
    } catch (error) {
        console.error('❌ Error fetching tournament details:', error);
        alert('❌ Ошибка при загрузке информации о турнире: ' + error.message);
        return;
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

    const age = document.getElementById('age').value;
    const phoneBrand = document.getElementById('phone-brand').value;
    const nickname = document.getElementById('nickname').value;
    const gameId = document.getElementById('game-id').value;

    if (!age || !phoneBrand || !nickname || !gameId) {
        alert('❌ Заполните все поля!');
        return;
    }

    // Валидация возраста
    const ageNum = parseInt(age);
    if (ageNum < 10 || ageNum > 99) {
        alert('❌ Возраст должен быть от 10 до 99 лет!');
        return;
    }

    console.log(`📝 Sending registration data:`, {
        user_id: currentUser.id,
        age: ageNum,
        phone_brand: phoneBrand,
        nickname: nickname,
        game_id: gameId,
        tournament_id: currentTournamentId
    });

    try {
        const response = await fetch(`/api/tournaments/${currentTournamentId}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUser.id,
                age: ageNum,
                phone_brand: phoneBrand,
                nickname: nickname,
                game_id: gameId
            })
        });

        console.log(`📡 Response status: ${response.status}`);

        const result = await response.json();
        console.log(`📋 Response data:`, result);

        if (result.success) {
            alert('✅ Вы успешно зарегистрированы в турнире!');
            await loadTournaments(); // Обновляем список
        } else {
            // Проверяем, нужна ли подписка
            if (result.subscription_required) {
                alert('❌ ' + result.error + '\n\n📢 Подпишитесь на наш канал и попробуйте снова!');
            } else {
                alert('❌ ' + (result.error || 'Ошибка регистрации'));
            }
        }
    } catch (error) {
        console.error('❌ Error registering for tournament:', error);
        alert('❌ Ошибка при регистрации в турнире');
    }
}

// Show admin panel
function showAdminPanel() {
    console.log('🔧 Showing admin panel - isAdmin:', isAdmin, 'currentUser:', currentUser);

    if (!isAdmin) {
        document.getElementById('admin-content').innerHTML = `
            <div class="error-message">
                <h3>❌ Доступ запрещен</h3>
                <p>У вас нет прав администратора</p>
                <p><small>Debug: isAdmin = ${isAdmin}, user = ${currentUser?.id}</small></p>
            </div>
        `;
        return;
    }

    document.getElementById('admin-content').innerHTML = `
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
            <div class="admin-card" onclick="showTournamentParticipantsSelector()">
                <div class="admin-card-icon">👥</div>
                <h3>Участники турниров</h3>
                <p>Просмотр участников конкретного турнира</p>
            </div>
            <div class="admin-card" onclick="loadAdminStats()">
                <div class="admin-card-icon">📊</div>
                <h3>Статистика</h3>
                <p>Просмотр статистики пользователей и активности</p>
            </div>
             <div class="admin-card" onclick="showTournamentRegistrationControl()">
                <div class="admin-card-icon">🔐</div>
                <h3>Закрыть/открыть регистрацию</h3>
                <p>Управление регистрацией на турниры</p>
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
            showAdminPanel();
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
             <div class="form-group">
                <label>Регистрация открыта</label>
                <select id="tournament-registration-status">
                    <option value="open">Да</option>
                    <option value="closed">Нет</option>
                </select>
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
    const registrationStatus = document.getElementById('tournament-registration-status').value; // Get registration status

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
        prizes: prizes,
        registration_open: registrationStatus === 'open' // Include registration status in data
    };

    try {
        const response = await fetch('/api/tournaments', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (result.success) {
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
        } else {
            alert('❌ ' + (result.error || 'Ошибка при удалении розыгрыша'));
        }
    } catch (error) {
        console.error('Error deleting giveaway:', error);
        alert('❌ Ошибка при удалении розыгрыша');
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

// Delete tournament function
async function deleteTournament(tournamentId) {
    if (!confirm('🗑️ Удалить турнир? Это действие нельзя отменить!\n\n⚠️ Все участники будут удалены!')) return;

    try {
        const response = await fetch(`/api/tournaments/${tournamentId}`, {
            method: 'DELETE'
        });

        const result = await response.json();
        if (result.success) {
            alert('✅ Турнир удален!');
            loadTournaments(); // Перезагружаем список турниров

            // Если мы в админ-панели, обновляем её тоже
            if (document.querySelector('.tournament-control-panel')) {
                showTournamentRegistrationControl();
            }
        } else {
            alert('❌ Ошибка при удалении турнира: ' + (result.error || 'Неизвестная ошибка'));
        }
    } catch (error) {
        console.error('Error deleting tournament:', error);
        alert('❌ Ошибка при удалении турнира');
    }
}


async function viewTournamentParticipants(tournamentId) {
    console.log(`👥 Loading participants for tournament ${tournamentId}`);

    if (!isAdmin) {
        alert('❌ У вас нет прав для просмотра участников');
        return;
    }

    // Показываем индикатор загрузки
    document.getElementById('admin-content').innerHTML = `
        <div class="participants-view">
            <div class="participants-header">
                <h2>👥 Участники турнира</h2>
                <button onclick="showTournamentParticipantsSelector()" class="back-btn">← Назад к списку</button>
            </div>
            <div class="loading">🔄 Загрузка участников...</div>
        </div>
    `;

    try {
        // Сначала получаем информацию о турнире
        console.log(`🏆 Fetching tournament ${tournamentId} info...`);
        const tournamentResponse = await fetch(`/api/tournaments/${tournamentId}`);

        if (!tournamentResponse.ok) {
            throw new Error(`Tournament not found: ${tournamentResponse.status}`);
        }

        const tournamentInfo = await tournamentResponse.json();
        console.log(`🏆 Tournament info:`, tournamentInfo);

        // Теперь получаем участников
        console.log(`👥 Fetching participants for tournament ${tournamentId}...`);
        const participantsResponse = await fetch(`/api/tournaments/${tournamentId}/participants`);

        if (!participantsResponse.ok) {
            throw new Error(`Failed to load participants: ${participantsResponse.status}`);
        }

        const participants = await participantsResponse.json();
        console.log(`📊 Loaded ${participants.length} participants:`, participants);

        if (!Array.isArray(participants)) {
            throw new Error('Invalid participants data format');
        }

        // Отображаем участников в админ-панели
        document.getElementById('admin-content').innerHTML = `
            <div class="participants-view">
                <div class="participants-header">
                    <h2>👥 Участники турнира: ${tournamentInfo.title || 'Без названия'}</h2>
                    <button onclick="showTournamentParticipantsSelector()" class="back-btn">← Назад к списку</button>
                </div>
                <div class="participants-stats">
                    <div class="stat-card">
                        <div class="stat-number">${participants.length}</div>
                        <div class="stat-label">Всего участников</div>
                    </div>
                </div>
                ${participants.length === 0 ? `
                    <div class="empty-state">
                        📝 На турнир пока никто не зарегистрировался
                        <br><br>
                        <small>Турнир: ${tournamentInfo.title}</small>
                        <br>
                        <small>Статус регистрации: ${tournamentInfo.registration_status === 'open' ? '🔓 Открыта' : '🔒 Закрыта'}</small>
                    </div>
                ` : `
                    <div class="participants-list">
                        ${participants.map((participant, index) => `
                            <div class="participant-card">
                                <div class="participant-number">${index + 1}</div>
                                <div class="participant-info">
                                    <div class="participant-name">${participant.first_name || participant.name || 'Без имени'}</div>
                                    <div class="participant-details">
                                        <span>🎮 ${participant.nickname || 'Не указан'}</span>
                                        <span>🆔 ${participant.game_id || 'Не указан'}</span>
                                        <span>📱 ${participant.phone_brand || 'Не указан'}</span>
                                        <span>🎂 ${participant.age || 'Не указан'} лет</span>
                                        ${participant.username ? `<span>👤 @${participant.username}</span>` : ''}
                                        <span>👤 ID: ${participant.user_id}</span>
                                    </div>
                                    <div class="participant-date">
                                        📅 ${participant.registration_date ? new Date(participant.registration_date).toLocaleDateString('ru-RU') : 'Дата не указана'}
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    <div class="participants-actions">
                        <button onclick="exportParticipants(${tournamentId})" class="export-btn">📊 Экспортировать список</button>
                        <button onclick="announceWinners(${tournamentId})" class="announce-btn">🏆 Объявить победителей</button>
                        <button onclick="showTournamentParticipantsSelector()" class="cancel-btn">🔙 Назад к турнирам</button>
                    </div>
                `}
            </div>
        `;

    } catch (error) {
        console.error('❌ Error loading participants:', error);
        document.getElementById('admin-content').innerHTML = `
            <div class="participants-view">
                <div class="participants-header">
                    <h2>👥 Участники турнира</h2>
                    <button onclick="showTournamentParticipantsSelector()" class="back-btn">← Назад к списку</button>
                </div>
                <div class="error-message">
                    ❌ Ошибка при загрузке участников
                    <br><br>
                    <small>Детали: ${error.message}</small>
                    <br><br>
                    <button onclick="viewTournamentParticipants(${tournamentId})" class="admin-btn">🔄 Повторить</button>
                    <button onclick="showTournamentParticipantsSelector()" class="cancel-btn">🔙 Назад</button>
                </div>
            </div>
        `;
    }
}

// Функция для объявления победителей
async function announceWinners(tournamentId) {
    const winnersText = prompt('🏆 Введите список победителей:\n\nНапример:\n🥇 1 место: Никнейм1\n🥈 2 место: Никнейм2\n🥉 3 место: Никнейм3');

    if (!winnersText || !winnersText.trim()) {
        alert('❌ Список победителей не может быть пустым');
        return;
    }

    try {
        const response = await fetch(`/api/tournaments/${tournamentId}/announce-winners`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ winners: winnersText.trim() })
        });

        const result = await response.json();
        if (result.success) {
            alert('✅ Победители объявлены и сообщение опубликовано в канале!');
        } else {
            alert('❌ Ошибка при объявлении победителей: ' + (result.error || 'Неизвестная ошибка'));
        }
    } catch (error) {
        console.error('Error announcing winners:', error);
        alert('❌ Ошибка при объявлении победителей');
    }
}

// Функция для экспорта участников
function exportParticipants(tournamentId) {
    const participantCards = document.querySelectorAll('.participant-card');
    let exportText = `📋 СПИСОК УЧАСТНИКОВ ТУРНИРА\n\n`;

    participantCards.forEach((card, index) => {
        const name = card.querySelector('.participant-name').textContent;
        const details = Array.from(card.querySelectorAll('.participant-details span')).map(span => span.textContent).join(' | ');
        exportText += `${index + 1}. ${name}\n   ${details}\n\n`;
    });

    // Пытаемся скопировать в буфер обмена
    if (navigator.clipboard) {
        navigator.clipboard.writeText(exportText).then(() => {
            alert('✅ Список участников скопирован в буфер обмена!');
        }).catch(() => {
            alert(exportText);
        });
    } else {
        alert(exportText);
    }
}

// Show tournament registration control panel
async function showTournamentRegistrationControl() {
    document.getElementById('admin-content').innerHTML = '<div class="loading">Загрузка турниров...</div>';

    try {
        const response = await fetch('/api/tournaments');
        const tournaments = await response.json();

        if (!tournaments || tournaments.length === 0) {
            document.getElementById('admin-content').innerHTML = `
                <div class="empty-state">
                    <h3>🤔 Нет турниров</h3>
                    <p>Сначала создайте турниры</p>
                    <button onclick="showAdminPanel()" class="admin-btn">🔙 Назад в админ панель</button>
                </div>
            `;
            return;
        }

        document.getElementById('admin-content').innerHTML = `
            <div class="tournament-control-panel">
                <h2>🔐 Управление регистрацией турниров</h2>
                <p class="control-description">Выберите турнир для управления регистрацией:</p>

                <div class="tournaments-control-list">
                    ${tournaments.map(tournament => {
                        // Правильно определяем статус
                        const status = tournament.registration_status || 'open';
                        const isClosed = status === 'closed';

                        return `
                        <div class="tournament-control-card">
                            <div class="tournament-control-info">
                                <h3>${tournament.title || 'Без названия'}</h3>
                                <p>${tournament.description || 'Без описания'}</p>
                                <div class="tournament-control-meta">
                                    <span>👥 ${tournament.participants || 0} участников</span>
                                    <span>📅 ${tournament.start_date ? new Date(tournament.start_date).toLocaleDateString('ru-RU') : 'Дата не указана'}</span>
                                    <span class="status-badge ${isClosed ? 'closed' : 'open'}">
                                        ${isClosed ? '🔒 Регистрация закрыта' : '✅ Регистрация открыта'}
                                    </span>
                                </div>
                            </div>
                            <div class="tournament-control-actions">
                                <button
                                    onclick="toggleTournamentRegistration(${tournament.id}, '${status}')"
                                    class="toggle-btn ${isClosed ? 'open' : 'close'}"
                                >
                                    ${isClosed ? '🔓 Открыть регистрацию' : '🔒 Закрыть регистрацию'}
                                </button>
                            </div>
                        </div>`;
                    }).join('')}
                </div>

                <div class="form-buttons">
                    <button onclick="showAdminPanel()" class="cancel-btn">🔙 Назад в админ панель</button>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading tournaments for control:', error);
        document.getElementById('admin-content').innerHTML = `
            <div class="empty-state">
                <h3>❌ Ошибка загрузки</h3>
                <p>Не удалось загрузить список турниров</p>
                <button onclick="showAdminPanel()" class="admin-btn">🔙 Назад в админ панель</button>
            </div>
        `;
    }
}

// Toggle tournament registration status
async function toggleTournamentRegistration(tournamentId, currentStatus) {
    // Определяем что мы хотим сделать
    const actionText = currentStatus === 'open' ? 'закрыть' : 'открыть';
    const newStatusText = currentStatus === 'open' ? 'закрыта' : 'открыта';

    if (!confirm(`Вы уверены, что хотите ${actionText} регистрацию на турнир?`)) {
        return;
    }

    try {
        console.log(`🔄 Toggling tournament ${tournamentId} - current status: ${currentStatus}`);

        const response = await fetch(`/api/tournaments/${tournamentId}/toggle-registration`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}) // Пустое тело, логика на сервере
        });

        const result = await response.json();
        console.log('📋 Toggle result:', result);

        if (result.success) {
            alert(`✅ Регистрация ${newStatusText}!`);

            // Обновляем список турниров во всех вкладках
            await loadTournaments();

            // Если мы в панели управления - обновляем её
            if (document.querySelector('.tournament-control-panel')) {
                showTournamentRegistrationControl();
            }
        } else {
            alert('❌ Ошибка при изменении статуса: ' + (result.error || 'Неизвестная ошибка'));
        }
    } catch (error) {
        console.error('Error toggling registration:', error);
        alert('❌ Ошибка при изменении статуса регистрации');
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

// Show tournament participants selector
async function showTournamentParticipantsSelector() {
    console.log('👥 Loading tournament participants selector...');

    try {
        document.getElementById('admin-content').innerHTML = '<div class="loading">Загрузка турниров...</div>';

        const response = await fetch('/api/tournaments');

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const tournaments = await response.json();
        console.log('🏆 Loaded tournaments for participants view:', tournaments);

        if (!Array.isArray(tournaments) || tournaments.length === 0) {
            document.getElementById('admin-content').innerHTML = `
                <div class="admin-stats">
                    <div class="stats-header">
                        <h2>👥 Участники турниров</h2>
                        <button onclick="showAdminPanel()" class="back-btn">← Назад</button>
                    </div>
                    <div class="empty-state">
                        📭 Пока нет созданных турниров
                        <br><br>
                        <button onclick="showCreateTournament()" class="admin-btn">➕ Создать турнир</button>
                    </div>
                </div>
            `;
            return;
        }

        const tournamentsList = tournaments.map(tournament => {
            const participantsCount = tournament.participants || 0;
            const formattedDate = tournament.start_date ?
                new Date(tournament.start_date).toLocaleDateString('ru-RU') :
                'Дата не указана';

            return `
            <div class="tournament-selector-card" onclick="viewTournamentParticipants(${tournament.id})">
                <div class="tournament-selector-info">
                    <h3>${tournament.title || 'Без названия'}</h3>
                    <p>${tournament.description || 'Без описания'}</p>
                    <div class="tournament-selector-stats">
                        <span>👥 ${participantsCount} участников</span>
                        <span>📅 ${formattedDate}</span>
                        <span class="status ${tournament.registration_status || 'open'}">
                            ${(tournament.registration_status || 'open') === 'open' ? '🔓 Открыт' : '🔒 Закрыт'}
                        </span>
                    </div>
                </div>
                <div class="tournament-selector-arrow">▶</div>
            </div>`;
        }).join('');

        document.getElementById('admin-content').innerHTML = `
            <div class="admin-stats">
                <div class="stats-header">
                    <h2>👥 Участники турниров</h2>
                    <button onclick="showAdminPanel()" class="back-btn">← Назад</button>
                </div>
                <div class="tournament-selector-subtitle">
                    Выберите турнир для просмотра участников:
                </div>
                <div class="tournament-selector-list">
                    ${tournamentsList}
                </div>
                <div class="participants-help">
                    💡 Нажмите на карточку турнира чтобы увидеть список участников
                </div>
            </div>
        `;

    } catch (error) {
        console.error('❌ Error loading tournaments for participants view:', error);
        document.getElementById('admin-content').innerHTML = `
            <div class="admin-stats">
                <div class="stats-header">
                    <h2>👥 Участники турниров</h2>
                    <button onclick="showAdminPanel()" class="back-btn">← Назад</button>
                </div>
                <div class="error-message">
                    ❌ Ошибка загрузки турниров
                    <br><br>
                    <small>Детали ошибки: ${error.message}</small>
                    <br><br>
                    <button onclick="showTournamentParticipantsSelector()" class="admin-btn">🔄 Повторить</button>
                </div>
            </div>
        `;
    }
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
                        <div class="stat-icon">🎯</div>
                        <div class="stat-info">
                            <div class="stat-number">${stats.active_giveaways || 0}</div>
                            <div class="stat-label">Активных розыгрышей</div>
                        </div>
                    </div>
                    <div class="compact-stat-card">
                        <div class="stat-icon">🎮</div>
                        <div class="stat-info">
                            <div class="stat-number">${stats.giveaway_participants || 0}</div>
                            <div class="stat-label">Участников розыгрышей</div>
                        </div>
                    </div>
                    <div class="compact-stat-card">
                        <div class="stat-icon">🏆</div>
                        <div class="stat-info">
                            <div class="stat-number">${stats.total_tournaments || 0}</div>
                            <div class="stat-label">Всего турниров</div>
                        </div>
                    </div>
                    <div class="compact-stat-card">
                        <div class="stat-icon">⚡</div>
                        <div class="stat-info">
                            <div class="stat-number">${stats.active_tournaments || 0}</div>
                            <div class="stat-label">Активных турниров</div>
                        </div>
                    </div>
                    <div class="compact-stat-card">
                        <div class="stat-icon">🏁</div>
                        <div class="stat-info">
                            <div class="stat-number">${stats.tournament_participants || 0}</div>
                            <div class="stat-label">Участников турниров</div>
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
document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOM loaded, initializing Telegram WebApp...');
    initTelegramWebApp();
    initializeApp();
});

// Window load event
window.addEventListener('load', function() {
    console.log('✅ Page loaded, re-initializing...');
    initTelegramWebApp();
    initializeApp();
});

console.log('🚀 Script.js loaded successfully');