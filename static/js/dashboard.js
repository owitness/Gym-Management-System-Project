window.onload = pageLoad;

function getAuthHeaders() {
    // First check for token in localStorage using the correct key
    let token = localStorage.getItem('gym_token');
    
    // If not found, try to get from URL query params (for initial load)
    if (!token) {
        const urlParams = new URLSearchParams(window.location.search);
        token = urlParams.get('token');
        
        // If found in URL, save to localStorage for future use
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

async function loadDashboardData() {
    try {
        const response = await fetch('/api/dashboard/summary', {
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to load dashboard data');
        const data = await response.json();
        const membership = data.membership;

        // Update the DOM with membership data
        document.getElementById('username').textContent = membership?.member_name || "Member";
        document.getElementById('email').textContent = membership?.email || "N/A";
        document.getElementById('address').textContent = membership?.address || "N/A";
        document.getElementById('membstatus').textContent = membership?.status || "N/A";
        document.getElementById('membtype').textContent = membership?.membership_type || "N/A";
        document.getElementById('expiration').textContent = membership?.expiration || "N/A";
        
        // Handle upcoming classes
        const classesList = document.getElementById('classes-list');
        if (data.upcoming_classes.length > 0) {
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
        // Update profile with data
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
        // Update membership info with data
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
        // Update classes with data
    } catch (error) {
        console.error('Error loading classes:', error);
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
    loadProfileData();
    loadMembershipData();
    loadClassesData();
});

function logout() {
    localStorage.removeItem('token');
    window.location.href = "/login";
}

// This function can be placed in a separate file or directly in the HTML, depending on your structure.
function pageLoad() {
    loadDashboardData();
}