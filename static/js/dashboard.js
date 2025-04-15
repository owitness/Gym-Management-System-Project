window.onload = pageLoad;

async function loadDashboardSummary() {
    const token = localStorage.getItem('token'); // Adjust if you're storing the token differently

    try {
        const response = await fetch('/dashboard/summary', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch dashboard data');
        }

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

function logout() {
    localStorage.clear();
    sessionStorage.clear();
    window.location.href = "/home";
}

// This function can be placed in a separate file or directly in the HTML, depending on your structure.
function pageLoad() {
    loadDashboardSummary();
}