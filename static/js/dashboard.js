// ==========================
// Authentication Utilities
// ==========================

function getAuthHeaders() {
    let token = localStorage.getItem('gym_token');

    if (!token) {
        const urlParams = new URLSearchParams(window.location.search);
        token = urlParams.get('token');

        if (token) {
            localStorage.setItem('gym_token', token);
        }
    }

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

    window.location.href = `/${route}?token=${token}`;
}

function navigateToCalendar() {
    const token = localStorage.getItem('gym_token');
    if (!token) {
        window.location.href = '/login';
        return;
    }
    window.location.href = `/calendar?token=${token}`;
}

function logout() {
    localStorage.removeItem('gym_token');
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
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get("token");

    if (token) {
        localStorage.setItem("gym_token", token);
        window.history.replaceState({}, document.title, window.location.pathname);
    }

    loadDashboardData();
    loadProfileData();
    loadMembershipData();
    loadClassesData();
});
