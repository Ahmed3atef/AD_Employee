// --- State Management ---
const app = document.getElementById('app');
const navbar = document.getElementById('navbar');

// --- 1. The Views (HTML Templates in JS) ---

function renderLogin() {
    // Hide navbar on login page
    navbar.classList.add('hidden');
    
    app.innerHTML = `
        <div class="login-card">
            <h2>Login</h2>
            <form id="loginForm">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" id="username" placeholder="Enter 'admin'" required>
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" id="password" placeholder="Enter 'password'" required>
                </div>
                <button type="submit" class="btn-primary">Sign In</button>
            </form>
            <p id="error-msg" style="color: red; text-align: center; margin-top: 10px;"></p>
        </div>
    `;

    // Attach Event Listener to the new form
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
}

function renderDashboard(username) {
    // Show navbar
    navbar.classList.remove('hidden');

    app.innerHTML = `
        <div class="dashboard-view">
            <h1>Welcome back, ${username}!</h1>
            <p style="margin-bottom: 20px; color: #666;">Here is your data from Django Rest Framework:</p>
            
            <div class="card">
                <h3>Project Status</h3>
                <p>All systems operational.</p>
            </div>
            
            <div class="card" style="border-left-color: #007bff;">
                <h3>Recent Activity</h3>
                <p>User logged in just now.</p>
            </div>
        </div>
    `;
}

// --- 2. The Logic (Controllers) ---

async function handleLogin(e) {
    e.preventDefault(); // Stop page refresh

    const userIn = document.getElementById('username').value;
    const passIn = document.getElementById('password').value;
    const errorMsg = document.getElementById('error-msg');

    // --- MOCK LOGIN LOGIC (Replace this with Fetch later) ---
    if (userIn === 'admin' && passIn === 'password') {
        
        // Simulating an API delay
        errorMsg.textContent = "Authenticating...";
        
        /* REAL DRF CODE WOULD GO HERE:
           const response = await fetch('/api/login/', { ... });
        */
        
        setTimeout(() => {
            renderDashboard(userIn);
        }, 500);

    } else {
        errorMsg.textContent = "Invalid credentials! Try 'admin' / 'password'";
    }
}

function handleLogout() {
    // Clear tokens/session logic would go here
    renderLogin();
}

// --- 3. Init ---
// Load the login page immediately when script runs
renderLogin();