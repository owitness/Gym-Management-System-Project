// Token management
const TOKEN_KEY = 'gym_token';
const REFRESH_TOKEN_KEY = 'gym_refresh_token';
const USER_KEY = 'gym_user';

function setTokens(accessToken, refreshToken) {
    localStorage.setItem(TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

function getTokens() {
    return {
        accessToken: localStorage.getItem(TOKEN_KEY),
        refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY)
    };
}

function clearTokens() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
}

function setUser(user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function getUser() {
    const user = localStorage.getItem(USER_KEY);
    return user ? JSON.parse(user) : null;
}

async function refreshAccessToken() {
    const { refreshToken } = getTokens();
    if (!refreshToken) {
        throw new Error('No refresh token available');
    }

    try {
        const response = await fetch('/api/auth/refresh-token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ refresh_token: refreshToken })
        });

        if (!response.ok) {
            throw new Error('Token refresh failed');
        }

        const data = await response.json();
        setTokens(data.access_token, data.refresh_token);
        return data.access_token;
    } catch (error) {
        clearTokens();
        window.location.href = '/login';
        throw error;
    }
}

// API request wrapper with token refresh
async function apiRequest(url, options = {}) {
    const { accessToken } = getTokens();
    
    if (!accessToken) {
        window.location.href = '/login';
        return;
    }

    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
        ...options.headers
    };

    try {
        const response = await fetch(url, { ...options, headers });
        
        if (response.status === 401) {
            const newAccessToken = await refreshAccessToken();
            headers['Authorization'] = `Bearer ${newAccessToken}`;
            return fetch(url, { ...options, headers });
        }

        return response;
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Authentication functions
async function login(email, password) {
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        if (!response.ok) {
            throw new Error('Login failed');
        }

        const data = await response.json();
        setTokens(data.access_token, data.refresh_token);
        setUser(data.user);
        
        // Redirect based on role
        if (data.user.role === 'admin') {
            window.location.href = '/admin/dashboard';
        } else if (data.user.role === 'trainer') {
            window.location.href = '/trainer/dashboard';
        } else {
            window.location.href = '/dashboard';
        }
    } catch (error) {
        console.error('Login error:', error);
        throw error;
    }
}

function logout() {
    clearTokens();
    window.location.href = '/login';
}

// Initialize token check on page load
document.addEventListener('DOMContentLoaded', async () => {
    const { accessToken, refreshToken } = getTokens();
    if (accessToken && refreshToken) {
        try {
            // Add auth header to all fetch requests
            const originalFetch = window.fetch;
            window.fetch = async function(url, options = {}) {
                if (!options.headers) {
                    options.headers = {};
                }
                
                // Don't add auth headers to auth routes
                if (!url.includes('/api/auth/login') && !url.includes('/api/auth/register')) {
                    options.headers['Authorization'] = `Bearer ${accessToken}`;
                }
                
                return originalFetch(url, options);
            };
            
            // Intercept all link clicks to add token to URL if needed
            document.addEventListener('click', function(e) {
                // Check if click target is a link or has a link parent
                let target = e.target;
                while (target && target.tagName !== 'A') {
                    target = target.parentElement;
                }
                
                if (target && target.tagName === 'A') {
                    const href = target.getAttribute('href');
                    // Only modify internal links
                    if (href && href.startsWith('/') && 
                        !href.startsWith('/api/') && 
                        !href.startsWith('/login') && 
                        !href.startsWith('/signup') && 
                        !href.includes('token=')) {
                        
                        e.preventDefault();
                        
                        // Special handling for dashboard link - even when hash is present
                        if (href === '/dashboard' || href === '/dashboard#') {
                            window.location.href = `/dashboard?token=${accessToken}`;
                            return;
                        }
                        
                        // Add token to URL
                        const separator = href.includes('?') ? '&' : '?';
                        window.location.href = `${href}${separator}token=${accessToken}`;
                    }
                }
            });
            
            await apiRequest('/api/auth/verify-token');
        } catch (error) {
            window.location.href = '/login';
        }
    }
}); 