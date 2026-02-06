// --- State Management ---
const app = document.getElementById('app');
const navbar = document.getElementById('navbar');

// Token management
const TokenManager = {
    setTokens(access, refresh) {
        localStorage.setItem('access_token', access);
        localStorage.setItem('refresh_token', refresh);
    },
    
    getAccessToken() {
        return localStorage.getItem('access_token');
    },
    
    getRefreshToken() {
        return localStorage.getItem('refresh_token');
    },
    
    clearTokens() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_data');
    },
    
    isAuthenticated() {
        return !!this.getAccessToken();
    },
    
    setUser(userData) {
        localStorage.setItem('user_data', JSON.stringify(userData));
    },
    
    getUser() {
        const userData = localStorage.getItem('user_data');
        return userData ? JSON.parse(userData) : null;
    }
};

// API Client
const API = {
    baseURL: 'http://127.0.0.1:8000/api/auth',
    
    async login(username, password) {
        const response = await fetch(`${this.baseURL}/login/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }
        
        return await response.json();
    },
    
    async authenticatedRequest(url, options = {}) {
        const token = TokenManager.getAccessToken();
        
        const response = await fetch(url, {
            ...options,
            headers: {
                ...options.headers,
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            }
        });
        
        if (response.status === 401) {
            // Token expired, redirect to login
            handleLogout();
            throw new Error('Session expired. Please login again.');
        }
        
        return response;
    }
};

// --- 1. The Views (HTML Templates in JS) ---

function renderLogin() {
    // Hide navbar on login page
    navbar.classList.add('hidden');
    
    app.innerHTML = `
        <div class="login-card">
            <h2>Active Directory Login</h2>
            <p style="text-align: center; color: #666; margin-bottom: 20px;">
                Login with your AD credentials
            </p>
            <form id="loginForm">
                <div class="form-group">
                    <label>Username</label>
                    <input 
                        type="text" 
                        id="username" 
                        placeholder="Administrator@eissa.local or admin" 
                        required
                        autocomplete="username"
                    >
                    <small style="color: #666; font-size: 12px;">
                        Enter your Active Directory username
                    </small>
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input 
                        type="password" 
                        id="password" 
                        placeholder="Enter your password" 
                        required
                        autocomplete="current-password"
                    >
                </div>
                <button type="submit" class="btn-primary" id="loginBtn">
                    Sign In
                </button>
            </form>
            <div id="error-msg" style="color: #dc3545; text-align: center; margin-top: 15px; font-size: 14px;"></div>
            <div id="success-msg" style="color: #28a745; text-align: center; margin-top: 15px; font-size: 14px;"></div>
        </div>
    `;

    // Attach Event Listener to the new form
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
}

function renderDashboard() {
    // Show navbar
    navbar.classList.remove('hidden');
    
    const userData = TokenManager.getUser();
    const username = userData ? userData.username : 'User';

    app.innerHTML = `
        <div class="dashboard-view">
            <h1>Welcome, ${username}!</h1>
            <p style="margin-bottom: 20px; color: #666;">
                You are successfully authenticated with Active Directory
            </p>
            
            <div class="card">
                <h3>🔐 Authentication Status</h3>
                <p><strong>Username:</strong> ${username}</p>
                <p><strong>Staff Access:</strong> ${userData?.is_staff ? 'Yes' : 'No'}</p>
                <p><strong>Admin Access:</strong> ${userData?.is_superuser ? 'Yes' : 'No'}</p>
                <p><strong>Joined:</strong> ${userData?.date_joined ? new Date(userData.date_joined).toLocaleDateString() : 'N/A'}</p>
            </div>
            
            <div class="card" style="border-left-color: #007bff;">
                <h3>📊 Quick Actions</h3>
                <p>• Access Django Admin Panel</p>
                <p>• Manage Employees</p>
                <p>• Transfer OUs</p>
                <p>• View Audit Logs</p>
            </div>
            
            <div class="card" style="border-left-color: #28a745;">
                <h3>💡 JWT Token Info</h3>
                <p>Your session is secured with JWT tokens</p>
                <p><small style="color: #666;">Access token expires in 5 minutes</small></p>
                <p><small style="color: #666;">Refresh token expires in 1 day</small></p>
            </div>
            
            <div style="margin-top: 20px; text-align: center;">
                <a href="/admin/" class="btn-primary" style="display: inline-block; text-decoration: none; padding: 12px 24px;">
                    Go to Admin Panel
                </a>
            </div>
        </div>
    `;
}

// --- 2. The Logic (Controllers) ---

async function handleLogin(e) {
    e.preventDefault(); // Stop page refresh

    const userIn = document.getElementById('username').value.trim();
    const passIn = document.getElementById('password').value;
    const errorMsg = document.getElementById('error-msg');
    const successMsg = document.getElementById('success-msg');
    const loginBtn = document.getElementById('loginBtn');

    // Clear previous messages
    errorMsg.textContent = '';
    successMsg.textContent = '';
    
    // Disable button and show loading
    loginBtn.disabled = true;
    loginBtn.textContent = 'Authenticating...';

    try {
        // Call Django API
        const response = await API.login(userIn, passIn);
        
        // Store tokens and user data
        TokenManager.setTokens(response.access, response.refresh);
        TokenManager.setUser(response.user);
        
        // Show success message
        successMsg.textContent = 'Login successful! Redirecting...';
        
        // Redirect to dashboard after a short delay
        setTimeout(() => {
            renderDashboard();
        }, 500);

    } catch (error) {
        // Show error message
        errorMsg.textContent = error.message || 'Login failed. Please try again.';
        
        // Re-enable button
        loginBtn.disabled = false;
        loginBtn.textContent = 'Sign In';
    }
}

function handleLogout() {
    // Clear tokens and user data
    TokenManager.clearTokens();
    
    // Redirect to login
    renderLogin();
}

// --- 3. Init ---
// Check if user is authenticated on page load
document.addEventListener('DOMContentLoaded', function() {
    if (TokenManager.isAuthenticated()) {
        // User has token, show dashboard
        renderDashboard();
    } else {
        // No token, show login
        renderLogin();
    }
});