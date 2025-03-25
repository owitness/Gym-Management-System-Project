// Authentication module
const auth = {
    // API endpoints
    endpoints: {
        login: '/api/login',
        logout: '/api/logout',
        profile: '/api/profile',
        register: '/api/register'
    },

    // Token management
    token: {
        get: () => localStorage.getItem('token'),
        set: (token) => localStorage.setItem('token', token),
        remove: () => localStorage.removeItem('token')
    },

    // User data management
    user: {
        get: () => JSON.parse(localStorage.getItem('user')),
        set: (user) => localStorage.setItem('user', JSON.stringify(user)),
        remove: () => localStorage.removeItem('user')
    },

    // Get headers for authenticated requests
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        // Add CSRF token if available
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        if (csrfToken) {
            headers['X-CSRF-Token'] = csrfToken;
        }
        
        // Add auth token if available
        const token = this.token.get();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        return headers;
    },

    // Register user
    async register(userData) {
        try {
            const response = await fetch(this.endpoints.register, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(userData)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Registration failed');
            }

            // Store token and user data
            this.token.set(data.token);
            this.user.set(data.user);

            return data;
        } catch (error) {
            console.error('Registration error:', error);
            throw error;
        }
    },

    // Login user
    async login(credentials) {
        try {
            const response = await fetch(this.endpoints.login, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(credentials)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Login failed');
            }

            // Store token and user data
            this.token.set(data.token);
            this.user.set(data.user);

            return data;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    },

    // Get user profile
    async getProfile() {
        try {
            const response = await fetch(this.endpoints.profile, {
                method: 'GET',
                headers: this.getHeaders()
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to fetch profile');
            }

            return data;
        } catch (error) {
            console.error('Profile error:', error);
            throw error;
        }
    },

    // Logout user
    async logout() {
        try {
            const response = await fetch(this.endpoints.logout, {
                method: 'POST',
                headers: this.getHeaders()
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Logout failed');
            }

            // Clear token and user data
            this.token.remove();
            this.user.remove();

            return data;
        } catch (error) {
            console.error('Logout error:', error);
            throw error;
        }
    },

    // Check if user is authenticated
    isAuthenticated() {
        const token = this.token.get();
        if (!token) return false;
        
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload.exp * 1000 > Date.now();
        } catch (error) {
            console.error('Token validation error:', error);
            return false;
        }
    },

    // Get user role
    getUserRole() {
        const user = this.user.get();
        return user ? user.role : null;
    },

    // Initialize authentication state
    init() {
        // Check token expiration
        if (!this.isAuthenticated()) {
            this.token.remove();
            this.user.remove();
        }

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
                    
                    const data = await this.login(credentials);
                    
                    // Redirect based on role
                    if (data.user.role === 'admin') {
                        window.location.href = '/admin';
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
            try {
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
                await auth.register(userData);
                window.location.href = '/dashboard';
            } catch (error) {
                alert(error.message);
            }
        });
    }

    // Logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            try {
                await auth.logout();
                window.location.href = '/login';
            } catch (error) {
                alert(error.message);
            }
        });
    }

    // Profile page
    const profileContainer = document.getElementById('profileContainer');
    if (profileContainer) {
        (async () => {
            try {
                const profile = await auth.getProfile();
                // Update profile UI with the fetched data
                Object.entries(profile).forEach(([key, value]) => {
                    const element = document.getElementById(`profile_${key}`);
                    if (element) {
                        if (key === 'membership_expiry' || key === 'created_at') {
                            element.textContent = value ? new Date(value).toLocaleDateString() : 'N/A';
                        } else {
                            element.textContent = value || 'N/A';
                        }
                    }
                });
            } catch (error) {
                alert(error.message);
            }
        })();
    }
}); 