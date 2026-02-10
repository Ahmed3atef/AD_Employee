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
    baseURL: 'http://127.0.0.1:8000/api',
    
    async login(username, password) {
        const response = await fetch(`${this.baseURL}/auth/login/`, {
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
    async getEmployeeProfile() {
        const response = await this.authenticatedRequest(
            `${this.baseURL}/employee/profile/`,
            { method: 'GET' }
        );
    
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to load profile');
        }
    
        return await response.json();
    },
    

    async authenticatedRequest(url, options = {}) {
        const token = TokenManager.getAccessToken();
        
        const response = await fetch(url, {
            ...options,
            headers: {
                ...options.headers,
                'Authorization': `JWT ${token}`,
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
                        placeholder="'username'@eissa.local or 'username" 
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

async function renderDashboard() {
    navbar.classList.remove('hidden');

    app.innerHTML = `
        <div class="dashboard-view">
            <h1>Employee Dashboard</h1>
            <p style="color:#666">Loading your profile...</p>
        </div>
    `;

    try {
        const profile = await API.getEmployeeProfile();

        app.innerHTML = `
            <div class="dashboard-view">
                <h1>Welcome, ${profile.display_name}</h1>

                <div class="card">
                    <h3>Basic Information</h3>
                    <p><strong>Username:</strong> ${profile.username}</p>
                    <p><strong>Email:</strong> ${profile.email}</p>
                    <p><strong>Phone:</strong> ${profile.phone || '-'}</p>
                    <p><strong>OU:</strong> ${profile.ou}</p>
                </div>

                <div class="card">
                    <h3>Employment Details</h3>
                    <p><strong>Full Name (EN):</strong> ${profile.full_name_en}</p>
                    <p><strong>Full Name (AR):</strong> ${profile.full_name_ar || '-'}</p>
                    <p><strong>Department:</strong> ${profile.department?.name || '-'}</p>
                    <p><strong>Job Title:</strong> ${profile.job_title?.title || '-'}</p>
                    <p><strong>Hire Date:</strong> ${profile.hire_date}</p>
                    <p><strong>NID:</strong> ${profile.nid || '-'}</p>
                </div>

                <div class="card">
                    <h3>Active Directory</h3>
                    <p><strong>Display Name:</strong> ${profile.display_name}</p>
                    <p><strong>Distinguished Name:</strong></p>
                    <code style="display:block; background:#f8f9fa; padding:10px; border-radius:6px;">
                        ${profile.distinguished_name}
                    </code>
                </div>

                
            </div>
        `;
    } catch (error) {
        app.innerHTML = `
            <div class="dashboard-view">
                <h2 style="color:#dc3545">Error</h2>
                <p>${error.message}</p>
                <button onclick="handleLogout()">Back to Login</button>
            </div>
        `;
    }
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