// Global variables
let currentUser = null;
let isAdmin = false;

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

// Enhanced tab functionality with smooth transitions - Global function
window.showTab = function(tabId, event) {
    const currentActive = document.querySelector('.tab-content.active');
    const targetTab = document.getElementById(tabId);

    // Safety checks
    if (!targetTab) {
        console.warn(`Tab with id "${tabId}" not found`);
        return;
    }

    if (currentActive && currentActive !== targetTab) {
        currentActive.style.opacity = '0';
        currentActive.style.transform = 'translateY(20px)';

        setTimeout(() => {
            currentActive.classList.remove('active');
            targetTab.classList.add('active');
            targetTab.style.opacity = '0';
            targetTab.style.transform = 'translateY(20px)';

            setTimeout(() => {
                targetTab.style.opacity = '1';
                targetTab.style.transform = 'translateY(0)';
            }, 50);
        }, 150);
    } else if (!currentActive) {
        targetTab.classList.add('active');
        targetTab.style.opacity = '1';
        targetTab.style.transform = 'translateY(0)';
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
};

// Load data when page loads with loading animations
document.addEventListener('DOMContentLoaded', function() {
    const loader = document.createElement('div');
    loader.innerHTML = `
        <div style="
            position: fixed;
            inset: 0;
            background: rgba(10, 10, 15, 0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            backdrop-filter: blur(10px);
        ">
            <div style="
                width: 60px;
                height: 60px;
                border: 3px solid rgba(255, 107, 107, 0.3);
                border-top: 3px solid #ff6b6b;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            "></div>
        </div>
    `;
    document.body.appendChild(loader);

    const spinCSS = document.createElement('style');
    spinCSS.textContent = '@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }';
    document.head.appendChild(spinCSS);

    Promise.all([
        checkAdminStatus(),
        loadGiveaways(),
        loadTournaments(),
        loadStats()
    ]).then(() => {
        displayUserInfo();
        // Initialize default tab with safety check
        setTimeout(() => {
            if (document.getElementById('giveaways')) {
                showTab('giveaways');
            }
            loader.remove();
        }, 100);
    }).catch(error => {
        console.error('Error during initialization:', error);
        loader.remove();
    });
});

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

        const data = await response.json();
        isAdmin = data.is_admin;

        if (isAdmin) {
            const adminTab = document.querySelector('.admin-only');
            adminTab.style.display = 'block';
            adminTab.style.animation = 'slideInRight 0.5s ease';
        }
    } catch (error) {
        console.error('Error checking admin status:', error);
    }
}

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

async function loadGiveaways() {
    try {
        const response = await fetch('/api/giveaways');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const giveaways = await response.json();

        const container = document.getElementById('giveaways-container');

        if (giveaways.length === 0) {
            container.innerHTML = '<div class="no-content"><svg class="icon icon-lg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20,12 20,22 4,22 4,12"></polyline><rect x="2" y="7" width="20" height="5"></rect><line x1="12" y1="22" x2="12" y2="7"></line></svg>Пока нет активных розыгрышей</div>';
            return;
        }

        container.innerHTML = giveaways.map((giveaway, index) => `
            <div class="giveaway-card" style="animation: slideInUp 0.5s ease ${index * 0.1}s both;">
                <h3 class="giveaway-title">${giveaway.title}</h3>
                <p class="giveaway-description">${giveaway.description}</p>
                <div class="giveaway-meta">
                    <span><svg class="icon icon-sm" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>До: ${new Date(giveaway.end_date).toLocaleDateString()}</span>
                    <span><svg class="icon icon-sm" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>Участники: ${giveaway.participants || 0}</span>
                </div>
                <button class="participate-btn" onclick="participateGiveaway(${giveaway.id}, this)">
                    <span><svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle></svg>Участвовать</span>
                </button>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading giveaways:', error);
        document.getElementById('giveaways-container').innerHTML = 
            '<div class="error">❌ Ошибка загрузки розыгрышей</div>';
    }
}

async function loadTournaments() {
    try {
        const response = await fetch('/api/tournaments');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const tournaments = await response.json();

        const container = document.getElementById('tournaments-container');

        if (tournaments.length === 0) {
            container.innerHTML = '<div class="no-content"><svg class="icon icon-lg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"></path><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"></path><path d="M4 22h16"></path><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"></path></svg>Пока нет активных турниров</div>';
            return;
        }

        container.innerHTML = tournaments.map((tournament, index) => `
            <div class="tournament-card" style="animation: slideInUp 0.5s ease ${index * 0.1}s both;">
                <h3 class="tournament-title">${tournament.title}</h3>
                <p class="tournament-description">${tournament.description}</p>
                <div class="tournament-meta">
                    <span><svg class="icon icon-sm" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"></path><path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"></path></svg>Начало: ${new Date(tournament.start_date).toLocaleDateString()}</span>
                    <span class="participants-count"><svg class="icon icon-sm" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>Участники: ${tournament.participants || 0}</span>
                </div>
                <div style="display: flex; gap: 12px;">
                    <button class="register-btn" onclick="registerTournament(${tournament.id}, this)" style="flex: 1;">
                        <span><svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13,2 3,14 12,14 11,22 21,10 12,10 13,2"></polygon></svg>Зарегистрироваться</span>
                    </button>
                    ${isAdmin ? `<button class="admin-btn" onclick="showParticipants(${tournament.id})" style="flex: 0 0 auto; padding: 15px; min-width: auto;"><span><svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg></span></button>` : ''}
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading tournaments:', error);
        document.getElementById('tournaments-container').innerHTML = 
            '<div class="error">❌ Ошибка загрузки турниров</div>';
    }
}

async function loadStats() {
    if (!isAdmin) return;

    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();

        const animateNumber = (element, target) => {
            let current = 0;
            const increment = target / 30;
            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    element.textContent = target;
                    clearInterval(timer);
                } else {
                    element.textContent = Math.floor(current);
                }
            }, 50);
        };

        setTimeout(() => {
            animateNumber(document.getElementById('total-users'), stats.total_users);
            animateNumber(document.getElementById('active-users'), stats.active_users);
        }, 500);

    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Enhanced modal functions
function showCreateGiveaway() {
    const modal = document.getElementById('giveaway-modal');
    modal.style.display = 'block';
    setTimeout(() => {
        modal.querySelector('.modal-content').style.transform = 'scale(1)';
        modal.querySelector('.modal-content').style.opacity = '1';
    }, 50);
}

function showCreateTournament() {
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

// Add CSS animations
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