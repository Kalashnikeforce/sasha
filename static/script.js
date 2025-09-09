// Global variables
let currentTab = 'dashboard';
let giveaways = [];
let tournaments = [];

// Tab Navigation
function showDashboard(event) {
    switchTab('dashboard', event);
    loadDashboardData();
}

function showGiveaways(event) {
    switchTab('giveaways', event);
    loadGiveaways();
}

function showTournaments(event) {
    switchTab('tournaments', event);
    loadTournaments();
}

function showStats(event) {
    switchTab('stats', event);
    loadStats();
}

function switchTab(tabName, event) {
    // Update active tab button
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    // Ensure event and event.target exist before trying to access them
    if (event && event.target) {
        event.target.closest('.tab-btn').classList.add('active');
    } else {
        // If no event (e.g., initial load), find the button by tabName
        const activeBtn = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }
    }

    // Hide all content sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.style.display = 'none';
    });

    // Show selected content section
    const selectedSection = document.getElementById(tabName);
    if (selectedSection) {
        selectedSection.style.display = 'block';
    }
    currentTab = tabName;
}

// Dashboard Functions
async function loadDashboardData() {
    try {
        const [giveawaysRes, tournamentsRes] = await Promise.all([
            fetch('/api/giveaways'),
            fetch('/api/tournaments')
        ]);

        // Check if responses are ok before parsing JSON
        if (!giveawaysRes.ok) throw new Error(`HTTP error! status: ${giveawaysRes.status}`);
        if (!tournamentsRes.ok) throw new Error(`HTTP error! status: ${tournamentsRes.status}`);

        const giveaways = await giveawaysRes.json();
        const tournaments = await tournamentsRes.json();

        // Update dashboard stats
        const totalGiveawaysEl = document.getElementById('total-giveaways');
        if (totalGiveawaysEl) totalGiveawaysEl.textContent = giveaways.length || 0;

        const totalTournamentsEl = document.getElementById('total-tournaments');
        if (totalTournamentsEl) totalTournamentsEl.textContent = tournaments.length || 0;

        // Calculate total participants
        let totalParticipants = 0;
        giveaways.forEach(g => totalParticipants += g.participants_count || 0);
        tournaments.forEach(t => totalParticipants += t.participants_count || 0);
        const totalParticipantsEl = document.getElementById('total-participants');
        if (totalParticipantsEl) totalParticipantsEl.textContent = totalParticipants;

        // Calculate active events
        const activeEvents = giveaways.filter(g => g.status !== 'completed').length + 
                            tournaments.filter(t => t.status !== 'completed').length;
        const activeEventsEl = document.getElementById('active-events');
        if (activeEventsEl) activeEventsEl.textContent = activeEvents;

    } catch (error) {
        console.error('Error loading dashboard data:', error);
        // Display error message on dashboard if elements exist
        const dashboardSection = document.getElementById('dashboard');
        if (dashboardSection) {
            dashboardSection.innerHTML = '<div class="error-message">❌ Ошибка загрузки данных дашборда</div>';
        }
    }
}

// Giveaways Functions
async function loadGiveaways() {
    const container = document.getElementById('giveaways-list');
    if (!container) return; // Exit if container not found
    container.innerHTML = '<div class="loading">Загрузка розыгрышей...</div>';

    try {
        const response = await fetch('/api/giveaways');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        giveaways = await response.json();

        if (!giveaways || giveaways.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>🎁 Нет розыгрышей</h3>
                    <p>Создайте первый розыгрыш!</p>
                    <button class="btn-primary" onclick="openCreateModal('giveaway')">Создать розыгрыш</button>
                </div>
            `;
            return;
        }

        container.innerHTML = giveaways.map(giveaway => `
            <div class="item-card">
                <div class="item-header">
                    <div>
                        <div class="item-title">${giveaway.title}</div>
                        <div class="item-description">${giveaway.description || 'Без описания'}</div>
                    </div>
                    <div class="item-actions">
                        <button class="btn-small btn-primary" onclick="viewParticipants('giveaway', ${giveaway.id})">
                            👥 Участники
                        </button>
                        <button class="btn-small btn-secondary" onclick="drawWinners(${giveaway.id})">
                            🎲 Розыгрыш
                        </button>
                        <button class="btn-small btn-danger" onclick="deleteGiveaway(${giveaway.id})">
                            🗑️ Удалить
                        </button>
                    </div>
                </div>
                <div class="item-stats">
                    <span>👥 ${giveaway.participants_count || 0} участников</span>
                    <span>🏆 ${giveaway.winners_count || 1} победителей</span>
                    <span>📅 ${giveaway.end_date ? new Date(giveaway.end_date).toLocaleDateString('ru-RU') : 'Без даты'}</span>
                    <span class="status ${giveaway.status || 'active'}">${getStatusText(giveaway.status)}</span>
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading giveaways:', error);
        container.innerHTML = '<div class="error-message">❌ Ошибка загрузки розыгрышей</div>';
    }
}

// Tournaments Functions
async function loadTournaments() {
    const container = document.getElementById('tournaments-list');
    if (!container) return; // Exit if container not found
    container.innerHTML = '<div class="loading">Загрузка турниров...</div>';

    try {
        const response = await fetch('/api/tournaments');
         if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        tournaments = await response.json();

        if (!tournaments || tournaments.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>🏆 Нет турниров</h3>
                    <p>Создайте первый турнир!</p>
                     <button class="btn-primary" onclick="openCreateModal('tournament')">Создать турнир</button>
                </div>
            `;
            return;
        }

        container.innerHTML = tournaments.map(tournament => `
            <div class="item-card">
                <div class="item-header">
                    <div>
                        <div class="item-title">${tournament.title}</div>
                        <div class="item-description">${tournament.description || 'Без описания'}</div>
                    </div>
                    <div class="item-actions">
                        <button class="btn-small btn-primary" onclick="viewParticipants('tournament', ${tournament.id})">
                            👥 Участники
                        </button>
                        <button class="btn-small btn-danger" onclick="deleteTournament(${tournament.id})">
                            🗑️ Удалить
                        </button>
                    </div>
                </div>
                <div class="item-stats">
                    <span>👥 ${tournament.participants_count || 0} участников</span>
                    <span>🏆 ${tournament.winners_count || 1} победителей</span>
                    <span>📅 ${tournament.start_date ? new Date(tournament.start_date).toLocaleDateString('ru-RU') : 'Без даты'}</span>
                    <span class="status ${tournament.status || 'active'}">${getStatusText(tournament.status)}</span>
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading tournaments:', error);
        container.innerHTML = '<div class="error-message">❌ Ошибка загрузки турниров</div>';
    }
}

// Stats Functions
async function loadStats() {
    const container = document.getElementById('stats-content');
    if (!container) return; // Exit if container not found
    container.innerHTML = '<div class="loading">Загрузка статистики...</div>';

    try {
        const [giveawaysRes, tournamentsRes] = await Promise.all([
            fetch('/api/giveaways'),
            fetch('/api/tournaments')
        ]);

        if (!giveawaysRes.ok) throw new Error(`HTTP error! status: ${giveawaysRes.status}`);
        if (!tournamentsRes.ok) throw new Error(`HTTP error! status: ${tournamentsRes.status}`);

        const giveaways = await giveawaysRes.json();
        const tournaments = await tournamentsRes.json();

        // Calculate detailed stats
        const totalGiveaways = giveaways.length;
        const totalTournaments = tournaments.length;
        const activeGiveaways = giveaways.filter(g => g.status !== 'completed').length;
        const activeTournaments = tournaments.filter(t => t.status !== 'completed').length;
        const completedGiveaways = giveaways.filter(g => g.status === 'completed').length;
        const completedTournaments = tournaments.filter(t => t.status === 'completed').length;

        let totalGiveawayParticipants = 0;
        let totalTournamentParticipants = 0;
        giveaways.forEach(g => totalGiveawayParticipants += g.participants_count || 0);
        tournaments.forEach(t => totalTournamentParticipants += t.participants_count || 0);

        container.innerHTML = `
            <div class="stats-overview">
                <div class="stat-card">
                    <div class="stat-icon">🎁</div>
                    <div class="stat-info">
                        <h3>${totalGiveaways}</h3>
                        <p>Всего розыгрышей</p>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">🟢</div>
                    <div class="stat-info">
                        <h3>${activeGiveaways}</h3>
                        <p>Активных розыгрышей</p>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">✅</div>
                    <div class="stat-info">
                        <h3>${completedGiveaways}</h3>
                        <p>Завершённых розыгрышей</p>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">👥</div>
                    <div class="stat-info">
                        <h3>${totalGiveawayParticipants}</h3>
                        <p>Участников розыгрышей</p>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">🏆</div>
                    <div class="stat-info">
                        <h3>${totalTournaments}</h3>
                        <p>Всего турниров</p>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">🟢</div>
                    <div class="stat-info">
                        <h3>${activeTournaments}</h3>
                        <p>Активных турниров</p>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">✅</div>
                    <div class="stat-info">
                        <h3>${completedTournaments}</h3>
                        <p>Завершённых турниров</p>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">👥</div>
                    <div class="stat-info">
                        <h3>${totalTournamentParticipants}</h3>
                        <p>Участников турниров</p>
                    </div>
                </div>
            </div>
        `;

    } catch (error) {
        console.error('Error loading stats:', error);
        container.innerHTML = '<div class="error-message">❌ Ошибка загрузки статистики</div>';
    }
}

// Modal Functions
function openCreateModal(type) {
    const modal = document.getElementById('create-modal');
    const title = document.getElementById('modal-title');
    const formFields = document.getElementById('form-fields');
    const submitButton = document.getElementById('modal-submit-btn');

    if (!modal) {
        console.error("Create modal element not found!");
        return;
    }

    title.textContent = type === 'giveaway' ? 'Создать розыгрыш' : 'Создать турнир';
    submitButton.onclick = () => type === 'giveaway' ? createGiveaway() : createTournament();

    if (type === 'giveaway') {
        formFields.innerHTML = `
            <div class="form-group">
                <label>Название розыгрыша *</label>
                <input type="text" id="giveaway-title" required placeholder="Введите название розыгрыша">
            </div>
            <div class="form-group">
                <label>Описание</label>
                <textarea id="giveaway-description" placeholder="Введите описание розыгрыша"></textarea>
            </div>
            <div class="form-group">
                <label>Дата окончания</label>
                <input type="datetime-local" id="giveaway-end-date">
            </div>
            <div class="form-group">
                <label>Количество победителей</label>
                <input type="number" id="giveaway-winners" min="1" value="1">
            </div>
        `;
    } else { // type === 'tournament'
        formFields.innerHTML = `
            <div class="form-group">
                <label>Название турнира *</label>
                <input type="text" id="tournament-title" required placeholder="Введите название турнира">
            </div>
            <div class="form-group">
                <label>Описание</label>
                <textarea id="tournament-description" placeholder="Введите описание турнира"></textarea>
            </div>
            <div class="form-group">
                <label>Дата начала</label>
                <input type="datetime-local" id="tournament-start-date">
            </div>
            <div class="form-group">
                <label>Количество победителей</label>
                <input type="number" id="tournament-winners" min="1" value="1">
            </div>
        `;
    }

    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeCreateModal() {
    const modal = document.getElementById('create-modal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        // Clear form fields
        const formFields = document.getElementById('form-fields');
        if (formFields) formFields.innerHTML = ''; 
    }
}

function closeParticipantsModal() {
    const modal = document.getElementById('participants-modal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Create Functions
async function createGiveaway() {
    const titleInput = document.getElementById('giveaway-title');
    const descriptionInput = document.getElementById('giveaway-description');
    const endDateInput = document.getElementById('giveaway-end-date');
    const winnersCountInput = document.getElementById('giveaway-winners');

    // Check if elements exist before accessing their values
    const title = titleInput ? titleInput.value : '';
    const description = descriptionInput ? descriptionInput.value : '';
    const endDate = endDateInput ? endDateInput.value : '';
    const winnersCount = winnersCountInput ? parseInt(winnersCountInput.value) : 1;

    if (!title.trim()) {
        alert('Пожалуйста, введите название розыгрыша');
        return;
    }

    try {
        const response = await fetch('/api/giveaways', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: title.trim(),
                description: description.trim(),
                end_date: endDate || null,
                winners_count: winnersCount || 1
            })
        });

        if (response.ok) {
            closeCreateModal();
            alert('✅ Розыгрыш успешно создан!');
            if (currentTab === 'giveaways') {
                loadGiveaways();
            }
            loadDashboardData(); // Update dashboard stats
        } else {
            const errorData = await response.json();
            alert(`❌ Ошибка при создании розыгрыша: ${errorData.error || response.statusText}`);
        }
    } catch (error) {
        console.error('Error creating giveaway:', error);
        alert('❌ Ошибка при создании розыгрыша');
    }
}

async function createTournament() {
    const titleInput = document.getElementById('tournament-title');
    const descriptionInput = document.getElementById('tournament-description');
    const startDateInput = document.getElementById('tournament-start-date');
    const winnersCountInput = document.getElementById('tournament-winners');

    // Check if elements exist before accessing their values
    const title = titleInput ? titleInput.value : '';
    const description = descriptionInput ? descriptionInput.value : '';
    const startDate = startDateInput ? startDateInput.value : '';
    const winnersCount = winnersCountInput ? parseInt(winnersCountInput.value) : 1;


    if (!title.trim()) {
        alert('Пожалуйста, введите название турнира');
        return;
    }

    try {
        const response = await fetch('/api/tournaments', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: title.trim(),
                description: description.trim(),
                start_date: startDate || null,
                winners_count: winnersCount || 1
            })
        });

        if (response.ok) {
            closeCreateModal();
            alert('✅ Турнир успешно создан!');
            if (currentTab === 'tournaments') {
                loadTournaments();
            }
            loadDashboardData(); // Update dashboard stats
        } else {
             const errorData = await response.json();
            alert(`❌ Ошибка при создании турнира: ${errorData.error || response.statusText}`);
        }
    } catch (error) {
        console.error('Error creating tournament:', error);
        alert('❌ Ошибка при создании турнира');
    }
}

// Delete Functions
async function deleteGiveaway(id) {
    if (!confirm('Вы уверены, что хотите удалить этот розыгрыш?')) {
        return;
    }

    try {
        const response = await fetch(`/api/giveaways/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            alert('✅ Розыгрыш удалён');
            loadGiveaways();
            loadDashboardData(); // Update dashboard stats
        } else {
            const errorData = await response.json();
            alert(`❌ Ошибка при удалении розыгрыша: ${errorData.error || response.statusText}`);
        }
    } catch (error) {
        console.error('Error deleting giveaway:', error);
        alert('❌ Ошибка при удалении розыгрыша');
    }
}

async function deleteTournament(id) {
    if (!confirm('Вы уверены, что хотите удалить этот турнир?')) {
        return;
    }

    try {
        const response = await fetch(`/api/tournaments/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            alert('✅ Турнир удалён');
            loadTournaments();
            loadDashboardData(); // Update dashboard stats
        } else {
            const errorData = await response.json();
            alert(`❌ Ошибка при удалении турнира: ${errorData.error || response.statusText}`);
        }
    } catch (error) {
        console.error('Error deleting tournament:', error);
        alert('❌ Ошибка при удалении турнира');
    }
}

// Participants Functions
async function viewParticipants(type, id) {
    const modal = document.getElementById('participants-modal');
    const title = document.getElementById('participants-title');
    const content = document.getElementById('participants-content');

    if (!modal || !title || !content) {
        console.error("Participants modal elements not found!");
        return;
    }

    title.textContent = `Участники ${type === 'giveaway' ? 'розыгрыша' : 'турнира'}`;
    content.innerHTML = '<div class="loading">Загрузка участников...</div>';

    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';

    try {
        const response = await fetch(`/api/${type}s/${id}/participants`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const participants = await response.json();

        if (!participants || participants.length === 0) {
            content.innerHTML = `
                <div class="empty-state">
                    <h3>👥 Нет участников</h3>
                    <p>Пока никто не зарегистрировался</p>
                </div>
            `;
            return;
        }

        content.innerHTML = `
            <div class="participants-header">
                <h4>Всего участников: ${participants.length}</h4>
                <button class="btn-small btn-primary" onclick="exportParticipants(${JSON.stringify(participants).replace(/"/g, '&quot;')})">
                    📋 Экспорт списка
                </button>
            </div>
            <div class="participants-list">
                ${participants.map((participant, index) => `
                    <div class="participant-item">
                        <span class="participant-number">${index + 1}.</span>
                        <div class="participant-info">
                            <div class="participant-name">
                                ${participant.first_name || ''} ${participant.last_name || ''}
                            </div>
                            <div class="participant-username">
                                ${participant.username ? '@' + participant.username : 'Без username'}
                            </div>
                            <div class="participant-id">ID: ${participant.user_id}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        // Ensure styles are added only once
        if (!document.getElementById('participants-styles')) {
            const style = document.createElement('style');
            style.id = 'participants-styles';
            style.textContent = `
                .participants-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 20px;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                }
                .participants-list {
                    max-height: 400px;
                    overflow-y: auto;
                    padding: 20px;
                }
                .participant-item {
                    display: flex;
                    align-items: center;
                    gap: 15px;
                    padding: 12px;
                    margin-bottom: 8px;
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 8px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }
                .participant-number {
                    font-weight: bold;
                    color: #4ecdc4;
                    min-width: 30px;
                }
                .participant-info {
                    flex: 1;
                }
                .participant-name {
                    font-weight: 600;
                    color: #ffffff;
                    margin-bottom: 2px;
                }
                .participant-username {
                    color: rgba(255, 255, 255, 0.7);
                    font-size: 0.9rem;
                }
                .participant-id {
                    color: rgba(255, 255, 255, 0.5);
                    font-size: 0.8rem;
                }
            `;
            document.head.appendChild(style);
        }

    } catch (error) {
        console.error('Error loading participants:', error);
        content.innerHTML = '<div class="error-message">❌ Ошибка загрузки участников</div>';
    }
}

function exportParticipants(participants) {
    const text = participants.map((p, index) => 
        `${index + 1}. ${p.first_name || ''} ${p.last_name || ''} ${p.username ? '@' + p.username : ''} (ID: ${p.user_id})`
    ).join('\n');

    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            alert('✅ Список участников скопирован в буфер обмена!');
        }).catch(err => {
            console.error('Failed to copy text: ', err);
            // Fallback for browsers that don't support clipboard API or in insecure contexts
            fallbackCopyTextToClipboard(text);
        });
    } else {
        fallbackCopyTextToClipboard(text);
    }
}

function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    // Avoid scrolling to bottom
    textArea.style.top = "0";
    textArea.style.left = "0";
    textArea.style.position = "fixed";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            alert('✅ Список участников скопирован!');
        } else {
             alert('❌ Не удалось скопировать список участников.');
        }
    } catch (err) {
        console.error('Fallback: Oops, unable to copy', err);
        alert('❌ Ошибка при копировании.');
    }
    document.body.removeChild(textArea);
}

// Draw Winners Function
async function drawWinners(giveawayId) {
    if (!confirm('Провести розыгрыш победителей? Это действие нельзя отменить.')) {
        return;
    }

    try {
        const response = await fetch(`/api/giveaways/${giveawayId}/draw`, {
            method: 'POST'
        });

        if (response.ok) {
            const result = await response.json();
            // Check if result and result.winners exist and is an array
            const winnerCount = (result && Array.isArray(result.winners)) ? result.winners.length : 0;
            alert(`✅ Розыгрыш проведён! Победители: ${winnerCount}`);
            loadGiveaways();
        } else {
            const error = await response.json();
            alert(`❌ Ошибка: ${error.error || response.statusText}`);
        }
    } catch (error) {
        console.error('Error drawing winners:', error);
        alert('❌ Ошибка при проведении розыгрыша');
    }
}

// Utility Functions
function getStatusText(status) {
    switch (status) {
        case 'completed': return '✅ Завершён';
        case 'active': return '🟢 Активен';
        default: return '🟢 Активен'; // Default to active if status is unknown or null
    }
}

function refreshData() {
    switch (currentTab) {
        case 'dashboard':
            loadDashboardData();
            break;
        case 'giveaways':
            loadGiveaways();
            break;
        case 'tournaments':
            loadTournaments();
            break;
        case 'stats':
            loadStats();
            break;
        default:
            console.warn('Unknown tab:', currentTab);
            break;
    }
    alert('✅ Данные обновлены!');
}

// Close modals when clicking outside
window.onclick = function(event) {
    const createModal = document.getElementById('create-modal');
    const participantsModal = document.getElementById('participants-modal');

    if (createModal && event.target === createModal) {
        closeCreateModal();
    }
    if (participantsModal && event.target === participantsModal) {
        closeParticipantsModal();
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeCreateModal();
        closeParticipantsModal();
    }
});

// Initial setup: Load dashboard data on page load
document.addEventListener('DOMContentLoaded', () => {
    // Set initial tab button active state
    const dashboardTabBtn = document.querySelector('.tab-btn[data-tab="dashboard"]');
    if (dashboardTabBtn) {
        dashboardTabBtn.classList.add('active');
    }
    // Load dashboard data
    loadDashboardData();
});