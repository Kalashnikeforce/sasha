
// Telegram Web App API
const tg = window.Telegram.WebApp;
tg.expand();

// Get user data from Telegram
const user = tg.initDataUnsafe?.user;

// Check if user is admin
let isAdmin = false;

// Initialize the app
document.addEventListener('DOMContentLoaded', async function() {
    if (user) {
        document.getElementById('user-info').innerHTML = `
            <h2>Привет, ${user.first_name}!</h2>
            <p>@${user.username || 'username не указан'}</p>
        `;
        
        // Check if user is admin
        try {
            const response = await fetch('/api/check-admin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: user.id
                })
            });
            const result = await response.json();
            isAdmin = result.is_admin;
            
            // Show admin panel if user is admin
            if (isAdmin) {
                const adminPanel = document.getElementById('admin-panel');
                if (adminPanel) {
                    adminPanel.style.display = 'block';
                }
            }
        } catch (error) {
            console.error('Error checking admin status:', error);
        }
    }
    
    loadGiveaways();
    loadTournaments();
});

// Check subscription status
async function checkSubscription() {
    if (!user) return false;
    
    try {
        const response = await fetch('/api/check-subscription', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: user.id
            })
        });
        
        const result = await response.json();
        return result.is_subscribed;
    } catch (error) {
        console.error('Error checking subscription:', error);
        return false;
    }
}

// Load giveaways
async function loadGiveaways() {
    try {
        const response = await fetch('/api/giveaways');
        const giveaways = await response.json();
        
        const container = document.getElementById('giveaways-container');
        container.innerHTML = '';
        
        giveaways.forEach(giveaway => {
            const card = createGiveawayCard(giveaway);
            container.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading giveaways:', error);
    }
}

// Load tournaments
async function loadTournaments() {
    try {
        const response = await fetch('/api/tournaments');
        const tournaments = await response.json();
        
        const container = document.getElementById('tournaments-container');
        container.innerHTML = '';
        
        tournaments.forEach(tournament => {
            const card = createTournamentCard(tournament);
            container.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading tournaments:', error);
    }
}

// Create giveaway card
function createGiveawayCard(giveaway) {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
        <h3>${giveaway.title}</h3>
        <p>${giveaway.description}</p>
        <p>Участников: ${giveaway.participants}</p>
        <p>Окончание: ${new Date(giveaway.end_date).toLocaleString()}</p>
        <button class="participate-btn" onclick="participateInGiveaway(${giveaway.id})">
            🎁 Участвовать
        </button>
        ${isAdmin ? `<button class="admin-btn" onclick="selectWinner(${giveaway.id})">Выбрать победителя</button>` : ''}
    `;
    
    return card;
}

// Create tournament card
function createTournamentCard(tournament) {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
        <h3>${tournament.title}</h3>
        <p>${tournament.description}</p>
        <p>Начало: ${new Date(tournament.start_date).toLocaleString()}</p>
        <button class="register-btn" onclick="registerForTournament(${tournament.id})">
            🏆 Зарегистрироваться
        </button>
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

// Register for tournament
async function registerForTournament(tournamentId) {
    if (!user) {
        tg.showAlert('Ошибка: пользователь не найден');
        return;
    }
    
    // Check subscription first
    const isSubscribed = await checkSubscription();
    if (!isSubscribed) {
        tg.showAlert('Для регистрации необходимо подписаться на канал!');
        tg.openTelegramLink('https://t.me/neizvestnyipabger');
        return;
    }
    
    // Set current tournament ID for the modal
    window.currentTournamentId = tournamentId;
    
    // Open registration modal
    openModal('tournament-reg-modal');
}

// Modal functions
function openModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Tab switching function
function showTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => {
        content.style.display = 'none';
    });
    
    // Remove active class from all tabs
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab content
    const selectedTab = document.getElementById(tabName);
    if (selectedTab) {
        selectedTab.style.display = 'block';
    }
    
    // Add active class to clicked tab
    const activeTab = document.querySelector(`[onclick="showTab('${tabName}')"]`);
    if (activeTab) {
        activeTab.classList.add('active');
    }
}

// Admin functions
function showCreateGiveaway() {
    openModal('giveaway-modal');
}

function showCreateTournament() {
    openModal('tournament-modal');
}

function openCreateGiveaway() {
    openModal('giveaway-modal');
}

function openCreateTournament() {
    openModal('tournament-modal');
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
            loadTournaments();
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
            loadTournaments();
        } else {
            tg.showAlert('Вы уже зарегистрированы на этот турнир!');
        }
    } catch (error) {
        console.error('Error registering for tournament:', error);
        tg.showAlert('Ошибка при регистрации на турнир');
    }
});

// Select winner function (admin only)
async function selectWinner(giveawayId) {
    if (!isAdmin) return;
    
    try {
        const response = await fetch(`/api/giveaways/${giveawayId}/select-winner`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            tg.showAlert(`Победитель выбран: ${result.winner.first_name}`);
            loadGiveaways();
        } else {
            tg.showAlert('Ошибка при выборе победителя');
        }
    } catch (error) {
        console.error('Error selecting winner:', error);
        tg.showAlert('Ошибка при выборе победителя');
    }
}

// Close modals when clicking outside
window.onclick = function(event) {
    const modals = document.getElementsByClassName('modal');
    for (let i = 0; i < modals.length; i++) {
        if (event.target == modals[i]) {
            modals[i].style.display = 'none';
        }
    }
}
