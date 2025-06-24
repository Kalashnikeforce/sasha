
// Initialize Telegram Web App
const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

const user = tg.initDataUnsafe?.user;
const ADMIN_IDS = [123456789]; // Replace with actual admin IDs

// Check if user is admin
const isAdmin = user && ADMIN_IDS.includes(user.id);
if (isAdmin) {
    document.querySelector('.admin-only').style.display = 'block';
}

// Tab functionality
function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    document.getElementById(tabName + '-tab').classList.add('active');
    event.target.classList.add('active');
    
    if (tabName === 'giveaways') {
        loadGiveaways();
    } else if (tabName === 'admin' && isAdmin) {
        loadStats();
    }
}

// Load giveaways
async function loadGiveaways() {
    try {
        const response = await fetch('/api/giveaways');
        const giveaways = await response.json();
        
        const container = document.getElementById('giveaways-list');
        container.innerHTML = '';
        
        if (giveaways.length === 0) {
            container.innerHTML = '<p style="text-align: center; opacity: 0.7;">Пока нет активных розыгрышей</p>';
            return;
        }
        
        giveaways.forEach(giveaway => {
            const card = createGiveawayCard(giveaway);
            container.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading giveaways:', error);
    }
}

// Create giveaway card
function createGiveawayCard(giveaway) {
    const card = document.createElement('div');
    card.className = 'giveaway-card';
    
    const endDate = new Date(giveaway.end_date).toLocaleString('ru-RU');
    
    card.innerHTML = `
        <div class="giveaway-title">${giveaway.title}</div>
        <div class="giveaway-description">${giveaway.description}</div>
        <div class="giveaway-meta">
            <span>📅 До: ${endDate}</span>
            <span class="participants-count">👥 ${giveaway.participants} участников</span>
        </div>
        <button class="participate-btn" onclick="participateInGiveaway(${giveaway.id})">
            🎮 Участвовать
        </button>
        ${isAdmin ? `<button class="admin-btn" onclick="drawWinner(${giveaway.id})" style="margin-top: 10px;">🎲 Выбрать победителя</button>` : ''}
    `;
    
    return card;
}

// Participate in giveaway
async function participateInGiveaway(giveawayId) {
    if (!user) {
        tg.showAlert('Ошибка: пользователь не найден');
        return;
    }
    
    // Check subscription first
    const isSubscribed = await checkSubscription();
    if (!isSubscribed) {
        tg.showAlert('Для участия необходимо подписаться на канал!');
        tg.openTelegramLink('https://t.me/neizvestnyipabger');
        return;
    }
    
    try {
        const response = await fetch(`/api/giveaways/${giveawayId}/participate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: user.id
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            tg.showAlert('Вы успешно участвуете в розыгрыше!');
            loadGiveaways(); // Refresh the list
        } else {
            tg.showAlert('Вы уже участвуете в этом розыгрыше!');
        }
    } catch (error) {
        console.error('Error participating:', error);
        tg.showAlert('Ошибка при участии в розыгрыше');
    }
}

// Check subscription (mock function - implement real check via bot)
async function checkSubscription() {
    // This should be implemented via bot API call
    // For now, return true for demo purposes
    return true;
}

// Draw winner (admin only)
async function drawWinner(giveawayId) {
    if (!isAdmin) return;
    
    try {
        const response = await fetch(`/api/giveaways/${giveawayId}/draw`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            const winner = result.winner;
            const winnerText = winner.username ? `@${winner.username} (${winner.name})` : winner.name;
            tg.showAlert(`🎉 Победитель: ${winnerText}`);
        } else {
            tg.showAlert('Нет участников для розыгрыша');
        }
    } catch (error) {
        console.error('Error drawing winner:', error);
        tg.showAlert('Ошибка при выборе победителя');
    }
}

// Load stats (admin only)
async function loadStats() {
    if (!isAdmin) return;
    
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        document.getElementById('total-users').textContent = stats.total_users;
        document.getElementById('active-users').textContent = stats.active_users;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Show create giveaway modal
function showCreateGiveaway() {
    if (!isAdmin) return;
    document.getElementById('giveaway-modal').style.display = 'block';
}

// Show create tournament modal
function showCreateTournament() {
    if (!isAdmin) return;
    document.getElementById('tournament-modal').style.display = 'block';
}

// Close modal
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Create giveaway form handler
document.getElementById('giveaway-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const title = document.getElementById('giveaway-title').value;
    const description = document.getElementById('giveaway-description').value;
    const endDate = document.getElementById('giveaway-end-date').value;
    
    try {
        const response = await fetch('/api/giveaways', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title,
                description,
                end_date: endDate
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            tg.showAlert('Розыгрыш создан и опубликован!');
            closeModal('giveaway-modal');
            document.getElementById('giveaway-form').reset();
            loadGiveaways();
        } else {
            tg.showAlert('Ошибка при создании розыгрыша');
        }
    } catch (error) {
        console.error('Error creating giveaway:', error);
        tg.showAlert('Ошибка при создании розыгрыша');
    }
});

// Create tournament form handler
document.getElementById('tournament-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const title = document.getElementById('tournament-title').value;
    const description = document.getElementById('tournament-description').value;
    const startDate = document.getElementById('tournament-start-date').value;
    
    try {
        const response = await fetch('/api/tournaments', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title,
                description,
                start_date: startDate
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            tg.showAlert('Турнир создан и опубликован!');
            closeModal('tournament-modal');
            document.getElementById('tournament-form').reset();
        } else {
            tg.showAlert('Ошибка при создании турнира');
        }
    } catch (error) {
        console.error('Error creating tournament:', error);
        tg.showAlert('Ошибка при создании турнира');
    }
});

// Tournament registration form handler
document.getElementById('tournament-reg-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const age = document.getElementById('user-age').value;
    const phoneBrand = document.getElementById('phone-brand').value;
    const nickname = document.getElementById('game-nickname').value;
    const gameId = document.getElementById('game-id').value;
    
    try {
        const tournamentId = window.currentTournamentId;
        const response = await fetch(`/api/tournaments/${tournamentId}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: user.id,
                age: parseInt(age),
                phone_brand: phoneBrand,
                nickname,
                game_id: gameId
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            tg.showAlert('Вы успешно зарегистрированы на турнир!');
            closeModal('tournament-reg-modal');
            document.getElementById('tournament-reg-form').reset();
        } else {
            tg.showAlert('Вы уже зарегистрированы на этот турнир!');
        }
    } catch (error) {
        console.error('Error registering for tournament:', error);
        tg.showAlert('Ошибка при регистрации на турнир');
    }
});

// Close modals when clicking outside
window.onclick = function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadGiveaways();
});
