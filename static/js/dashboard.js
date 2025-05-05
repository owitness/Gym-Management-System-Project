// ==========================
// Authentication Utilities
// ==========================

/**
 * Checks and ensures proper token availability for authentication
 * Returns the token if available
 */
function ensureAuthentication() {
    // First try to get token from URL
    const urlParams = new URLSearchParams(window.location.search);
    const urlToken = urlParams.get("token");
    
    // Then try localStorage
    const localToken = localStorage.getItem("gym_token");
    
    // If token in URL, save to localStorage and return it
    if (urlToken) {
        localStorage.setItem("gym_token", urlToken);
        
        // Also set a cookie for server-side use on page refresh
        document.cookie = `token=${urlToken}; path=/; max-age=86400; SameSite=Strict`;
        
        // Always remove token from URL for security
        window.history.replaceState({}, document.title, window.location.pathname);
        
        return urlToken;
    }
    
    // If token in localStorage but not in URL
    if (localToken && !urlToken) {
        // Set a cookie for server-side use on page refresh
        document.cookie = `token=${localToken}; path=/; max-age=86400; SameSite=Strict`;
        
        // No longer add token to URL to prevent security issues
        return localToken;
    }
    
    // No token found - redirect to login
    window.location.href = '/login';
    return null;
}

/**
 * Get authentication headers for API calls
 */
function getAuthHeaders() {
    const token = localStorage.getItem('gym_token');
    
    const headers = {
        'Content-Type': 'application/json'
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
}

// ==========================
// Navigation Functions
// ==========================

function navigateTo(route) {
    const token = localStorage.getItem('gym_token');
    if (!token) {
        window.location.href = '/login';
        return;
    }

    if (route === 'dashboard' && window.location.pathname === '/dashboard') {
        return;
    }

    // Navigate without exposing token in URL
    window.location.href = `/${route}`;
}

function navigateToHome() {
    // Navigate to home page without losing authentication
    window.location.href = '/';
}

function navigateToCalendar() {
    const token = localStorage.getItem('gym_token');
    if (!token) {
        window.location.href = '/login';
        return;
    }
    // Navigate without exposing token in URL
    window.location.href = `/calendar`;
}

function logout() {
    // Clear all token storage methods
    localStorage.removeItem('gym_token');
    localStorage.removeItem('token');
    
    // Clear cookies
    document.cookie = 'token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    document.cookie = 'gym_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    
    // Redirect to login
    window.location.href = "/login";
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// ==========================
// Dashboard Data Loaders
// ==========================

async function loadDashboardData() {
    try {
        const response = await fetch('/api/dashboard/summary', {
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to load dashboard data');
        const data = await response.json();
        const membership = data.membership;

        // Update Personal Info
        document.getElementById('username').textContent = membership?.member_name || "Member";
        document.getElementById('fullname').textContent = membership?.member_name || "Member";
        document.getElementById('email').textContent = membership?.email || "N/A";
        document.getElementById('address').textContent = membership?.address || "N/A";
        


        // Update Membership Info dynamically
        const membershipInfo = document.getElementById('membership-info');
        membershipInfo.innerHTML = `
            <div class="info-item">
                <p>Status: <span class="badge ${membership.status}">${membership.status}</span></p>
                <p>Expiration: ${membership.expiration ? new Date(membership.expiration).toLocaleDateString() : "N/A"}</p>
            </div>
        `;

        // Add Cancel Membership Button
        const cancelBtn = document.createElement('button');
        cancelBtn.class = 'btn-primary';
        cancelBtn.className = 'btn-danger';
        cancelBtn.textContent = 'Cancel Membership';
        cancelBtn.addEventListener('click', cancelMembership);
        membershipInfo.appendChild(cancelBtn);

        // Update Upcoming Classes
        const classesList = document.getElementById('classes-list');
        if (data.upcoming_classes.length > 0) {
            classesList.innerHTML = '';
            data.upcoming_classes.forEach(classInfo => {
                const listItem = document.createElement('p');
                listItem.textContent = `${classInfo.class_name} (Trainer: ${classInfo.trainer_name}) - ${new Date(classInfo.schedule_time).toLocaleString()}`;
                classesList.appendChild(listItem);
            });
        } else {
            classesList.innerHTML = "<p>No upcoming classes found.</p>";
        }

    } catch (error) {
        console.error('Error loading dashboard:', error);
        alert('Could not load dashboard information.');
    }
}

async function loadProfileData() {
    try {
        const response = await fetch('/api/dashboard/profile', {
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to load profile data');
        const data = await response.json();
        // Profile info is now mainly handled by loadDashboardData()
    } catch (error) {
        console.error('Error loading profile:', error);
    }
}

async function loadMembershipData() {
    try {
        const response = await fetch('/api/my-membership', {
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to load membership data');
        const data = await response.json();
        // Membership info is mainly handled by loadDashboardData()
    } catch (error) {
        console.error('Error loading membership:', error);
    }
}

async function loadClassesData() {
    try {
        const response = await fetch('/api/classes', {
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to load classes data');
        const data = await response.json();
        // Class booking is handled separately
    } catch (error) {
        console.error('Error loading classes:', error);
    }
}

// ==========================
// Cancel Membership
// ==========================

async function cancelMembership() {
    if (!confirm("Are you absolutely sure you want to cancel your membership and delete your account?")) return;

    try {
        const response = await fetch('/api/memberships/cancel', {
            method: 'POST',
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'Failed to cancel membership');
        }

        alert("Your account has been deleted. Thank you for being with us.");
        localStorage.removeItem('gym_token'); // Clear the token
        window.location.href = "/";
    } catch (error) {
        console.error('Error cancelling membership:', error);
        alert('Error cancelling membership: ' + error.message);
    }
}

// ==========================
// Initializer
// ==========================

document.addEventListener('DOMContentLoaded', () => {
    // Ensure user is authenticated before loading dashboard data
    const token = ensureAuthentication();
    if (!token) return; // If no token, we've already redirected to login
    
    // Load dashboard data
    loadDashboardData();
    loadProfileData();
    loadMembershipData();
    loadClassesData();
});
