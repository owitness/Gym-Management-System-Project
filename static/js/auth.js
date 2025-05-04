// Authentication module
const auth = {
    // API endpoints
    endpoints: {
        register: '/api/auth/register',
        profile: '/api/auth/profile'
    },

    // Register user
    async register(userData) {
        try {
            const response = await fetch(this.endpoints.register, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(userData)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Registration failed');
            }

            setUser(data.user);
            setTokens(data.token, null); // Set the token from registration
            return data;
        } catch (error) {
            console.error('Registration error:', error);
            throw error;
        }
    },

    // Get user profile
    async getProfile() {
        try {
            const response = await apiRequest(this.endpoints.profile);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to fetch profile');
            }

            setUser(data.user);
            return data;
        } catch (error) {
            console.error('Profile error:', error);
            throw error;
        }
    },

    // Get user role
    getUserRole() {
        const user = getUser();
        return user ? user.role : null;
    },

    // Initialize authentication state
    init() {
        // Setup login form handler
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const errorMessage = document.getElementById('error-message');
                const loading = document.getElementById('loading');
                
                try {
                    loading.style.display = 'block';
                    errorMessage.style.display = 'none';
                    
                    const credentials = {
                        email: loginForm.email.value,
                        password: loginForm.password.value
                    };
                    
                    await login(credentials.email, credentials.password);
                } catch (error) {
                    errorMessage.textContent = error.message;
                    errorMessage.style.display = 'block';
                } finally {
                    loading.style.display = 'none';
                }
            });
        }
    }
};

// Initialize authentication state when the script loads
auth.init();

// Event listeners for forms
document.addEventListener('DOMContentLoaded', () => {
    // Registration form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const errorMessage = document.getElementById('error-message');
            const loading = document.getElementById('loading');
            
            try {
                loading.style.display = 'block';
                errorMessage.style.display = 'none';
                
                const userData = {
                    name: registerForm.name.value,
                    email: registerForm.email.value,
                    password: registerForm.password.value,
                    dob: registerForm.dob.value,
                    address: registerForm.address.value,
                    city: registerForm.city.value,
                    state: registerForm.state.value,
                    zipcode: registerForm.zipcode.value,
                    auto_payment: registerForm.auto_payment.checked
                };
                
                const response = await auth.register(userData);
                
                // Redirect based on role
                if (response.user.role === 'admin') {
                    window.location.href = '/admin/dashboard';
                } else if (response.user.role === 'trainer') {
                    window.location.href = '/trainer/dashboard';
                } else {
                    window.location.href = '/dashboard';
                }
            } catch (error) {
                errorMessage.textContent = error.message;
                errorMessage.style.display = 'block';
            } finally {
                loading.style.display = 'none';
            }
        });
    }

    // Logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    }
}); 