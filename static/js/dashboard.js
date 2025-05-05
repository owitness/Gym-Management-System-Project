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
    // Navigate with token in URL for initial load
    window.location.href = `/calendar?token=${encodeURIComponent(token)}`;
}

function logout() {
    // Clear all token storage methods
    localStorage.removeItem('gym_token');
    localStorage.removeItem('token');
    localStorage.removeItem('gym_refresh_token');
    localStorage.removeItem('gym_user');
    
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
        
        console.log('Dashboard summary data:', data);
        console.log('Upcoming classes:', data.upcoming_classes);
        
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

        // Update Upcoming Classes with timezone adjustment and cancel button
        const classesList = document.getElementById('classes-list');
        if (data.upcoming_classes && data.upcoming_classes.length > 0) {
            console.log('Rendering classes:', data.upcoming_classes);
            classesList.innerHTML = '';
            data.upcoming_classes.forEach(classInfo => {
                // Add 4 hours to the class time
                const classTime = new Date(classInfo.schedule_time);
                classTime.setHours(classTime.getHours() + 4);
                
                console.log('Class info:', classInfo);
                console.log('Class ID:', classInfo.id);
                
                const listItem = document.createElement('div');
                listItem.className = 'class-item';
                listItem.innerHTML = `
                    <p>${classInfo.class_name} (Trainer: ${classInfo.trainer_name}) - ${classTime.toLocaleString()}</p>
                    <button class="btn-danger cancel-class-btn" data-class-id="${classInfo.id}">Cancel</button>
                `;
                
                // Add event listener after the element is created
                const cancelBtn = listItem.querySelector('.cancel-class-btn');
                if (cancelBtn) {
                    cancelBtn.addEventListener('click', function() {
                        const classId = this.getAttribute('data-class-id');
                        console.log('Cancel button clicked for class ID:', classId);
                        showCancelClassModal(classId);
                    });
                }
                
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
        
        // Clear all tokens and session data
        localStorage.removeItem('gym_token');
        localStorage.removeItem('token');
        localStorage.removeItem('gym_refresh_token');
        localStorage.removeItem('gym_user');
        
        // Clear cookies with proper path and domain settings
        document.cookie = 'token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT; SameSite=Strict;';
        document.cookie = 'gym_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT; SameSite=Strict;';
        
        // Call logout API to invalidate server-side session
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
        } catch (e) {
            console.error('Error logging out:', e);
            // Continue with redirect even if logout API fails
        }
        
        // Force page reload to clear any in-memory state
        window.location.href = "/";
        window.location.reload(true);
    } catch (error) {
        console.error('Error cancelling membership:', error);
        alert('Error cancelling membership: ' + error.message);
    }
}

// ==========================
// Cancel Class Modal
// ==========================

// Add cancel class modal to the HTML
function addCancelClassModal() {
    // Check if modal already exists
    if (document.getElementById('cancel-class-modal')) {
        return;
    }

    const modal = document.createElement('div');
    modal.id = 'cancel-class-modal';
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <span class="close" onclick="closeCancelClassModal()">&times;</span>
            <h2>Cancel Class Booking</h2>
            <p>Are you sure you want to cancel this sign up?</p>
            <div class="modal-buttons">
                <button onclick="confirmCancelClass()" class="btn-danger">Yes</button>
                <button onclick="closeCancelClassModal()" class="btn-secondary">No</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

// Show cancel class modal
function showCancelClassModal(classId) {
    console.log('Showing cancel modal for class:', classId); // Debug log
    
    if (!classId) {
        console.error('No class ID provided to showCancelClassModal');
        alert('Error: Could not identify the class to cancel');
        return;
    }
    
    // Ensure modal exists
    addCancelClassModal();
    
    const modal = document.getElementById('cancel-class-modal');
    if (!modal) {
        console.error('Cancel class modal not found');
        return;
    }
    
    // Store the class ID in the modal as an attribute and in a hidden input
    modal.dataset.classId = classId;
    
    // If there's no hidden input for class ID, create one
    if (!modal.querySelector('#cancel-class-id')) {
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.id = 'cancel-class-id';
        hiddenInput.value = classId;
        modal.querySelector('.modal-content').appendChild(hiddenInput);
    } else {
        // Update existing hidden input
        modal.querySelector('#cancel-class-id').value = classId;
    }
    
    console.log('Stored class ID in modal:', modal.dataset.classId); // Debug log
    console.log('Stored class ID in hidden input:', modal.querySelector('#cancel-class-id')?.value); // Debug log
    
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden'; // Prevent background scrolling
}

// Close cancel class modal
function closeCancelClassModal() {
    const modal = document.getElementById('cancel-class-modal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto'; // Restore background scrolling
    }
}

// Confirm and process class cancellation
async function confirmCancelClass() {
    const modal = document.getElementById('cancel-class-modal');
    if (!modal) {
        console.error('Cancel class modal not found');
        return;
    }
    
    // Try to get class ID from multiple sources
    let classId = modal.dataset.classId;
    
    // If not found in dataset, try the hidden input
    if (!classId) {
        const hiddenInput = modal.querySelector('#cancel-class-id');
        if (hiddenInput) {
            classId = hiddenInput.value;
        }
    }
    
    console.log('Retrieved class ID from modal:', classId); // Debug log
    
    if (!classId || classId === 'undefined') {
        console.error('No class ID found for cancellation');
        alert('Error: Could not identify the class to cancel');
        return;
    }
    
    try {
        console.log('Sending cancel request for class:', classId); // Debug log
        const response = await fetch(`/api/classes/${classId}/cancel`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });

        console.log('Cancel response status:', response.status);
        
        if (!response.ok) {
            let errorMessage = 'Failed to cancel class booking';
            try {
                const errorData = await response.json();
                errorMessage = errorData.error || errorMessage;
            } catch (e) {
                console.error('Error parsing error response:', e);
            }
            throw new Error(errorMessage);
        }

        // Close the modal
        closeCancelClassModal();
        
        // Reload dashboard data to update the class list
        loadDashboardData();
        
        // Show success message
        alert('Class booking cancelled successfully');
        
    } catch (error) {
        console.error('Error cancelling class:', error);
        alert(`Failed to cancel class booking: ${error.message}`);
    }
}

// Add styles for the cancel class modal
function addCancelClassStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .class-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .cancel-class {
            margin-left: 10px;
            font-size: 1.2em;
        }
        
        .modal-buttons {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 20px;
        }
        
        .modal-buttons button {
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        
        .btn-danger {
            background-color: #dc3545;
            color: white;
        }
        
        .btn-secondary {
            background-color: #6c757d;
            color: white;
        }
    `;
    document.head.appendChild(style);
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

    // Initialize cancel class functionality
    addCancelClassStyles();
});
