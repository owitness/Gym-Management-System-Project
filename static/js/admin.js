// 🔹 Save token from URL or localStorage to cookie
(function saveTokenToCookie() {
    const urlParams = new URLSearchParams(window.location.search);
    const urlToken = urlParams.get("token");

    if (urlToken) {
        localStorage.setItem("gym_token", urlToken);
        document.cookie = `token=${urlToken}; path=/; max-age=86400; SameSite=Strict`;
        window.history.replaceState({}, document.title, window.location.pathname);
        return;
    }

    const localToken = localStorage.getItem("gym_token") || localStorage.getItem("token");
    if (localToken) {
        document.cookie = `token=${localToken}; path=/; max-age=86400; SameSite=Strict`;
    }
})();

// 🔹 DOMContentLoaded setup
window.addEventListener("DOMContentLoaded", () => {
    console.log("DOMContentLoaded - Initializing dashboard...");
    initRepairOrderButtons();
    loadClasses();
    populateTrainerDropdown();
    setupLogout();
    loadRepairReports();
    initializeDashboard();
    
    // Debug code to check if event listeners are properly attached
    console.log("Checking button elements:");
    console.log("Update Role Button:", document.getElementById('updateRoleBtn'));
    console.log("Delete Employee Button:", document.getElementById('deleteEmployeeBtn'));
    console.log("Update User Role Button:", document.getElementById('updateUserRoleBtn'));
    console.log("Delete User Button:", document.getElementById('deleteUserBtn'));
    
    // Ensure tokens are available
    console.log("Token availability:");
    console.log("localStorage.token:", localStorage.getItem('token'));
    console.log("localStorage.gym_token:", localStorage.getItem('gym_token'));
});

// 🔹 Repair Order Button Logic
function initRepairOrderButtons() {
    document.querySelectorAll(".repair-status").forEach(status => {
        status.classList.remove("open", "closed");
        status.classList.add("closed");
        status.textContent = "Pending";
    });

    document.querySelectorAll(".repair-action-btn").forEach(button => {
        button.addEventListener("click", event => {
            event.preventDefault();
            const row = button.closest("tr");
            const statusCell = row.querySelector(".repair-status");

            if (statusCell.classList.contains("closed") || statusCell.textContent === "Pending") {
                statusCell.classList.replace("closed", "open");
                statusCell.textContent = "In Progress";
                button.textContent = "Mark as Complete";
            } else if (statusCell.classList.contains("open")) {
                statusCell.classList.replace("open", "complete");
                statusCell.textContent = "Completed";
                button.textContent = "Archive";
            } else if (statusCell.classList.contains("complete")) {
                statusCell.classList.replace("complete", "archive");
                statusCell.textContent = "Archived";
                button.textContent = "Archived";
                button.disabled = true;
            }
        });
    });
}

// 🔹 Fetch and display classes
async function fetchClasses() {
    try {
        const token = localStorage.getItem("token");
        if (!token) throw new Error("No token");

        const res = await fetch("/api/classes", {
            headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error("Failed to fetch classes");
        return await res.json();
    } catch (e) {
        console.error("Error fetching classes:", e);
        return [];
    }
}

let currentPage = 1;
const itemsPerPage = 10;
let totalClasses = 0;

async function loadClasses() {
    const classes = await fetchClasses();
    totalClasses = classes.length;
    const totalPages = Math.ceil(totalClasses / itemsPerPage);
    
    // Update pagination info
    document.getElementById('pageInfo').textContent = `Page ${currentPage} of ${totalPages}`;
    document.getElementById('prevPage').disabled = currentPage === 1;
    document.getElementById('nextPage').disabled = currentPage === totalPages;
    
    // Calculate start and end indices for current page
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, totalClasses);
    
    const tbody = document.querySelector("#classList table tbody");
    tbody.innerHTML = "";

    // Sort classes by schedule_time
    classes.sort((a, b) => new Date(a.schedule_time) - new Date(b.schedule_time));

    // Display only classes for current page
    for (let i = startIndex; i < endIndex; i++) {
        const cls = classes[i];
        const tr = document.createElement("tr");
        
        // Add 4 hours to the class time
        const classTime = new Date(cls.schedule_time);
        classTime.setHours(classTime.getHours() + 4);
        
        tr.innerHTML = `
            <td>${cls.class_name}</td>
            <td>${cls.trainer_name}</td>
            <td>${classTime.toLocaleString()}</td>
            <td>${cls.capacity}</td>
            <td>${cls.current_bookings}</td>
            <td>${cls.capacity - cls.current_bookings}</td>
        `;
        tbody.appendChild(tr);
    }
}

// Add pagination event listeners
document.getElementById('prevPage').addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        loadClasses();
    }
});

document.getElementById('nextPage').addEventListener('click', () => {
    const totalPages = Math.ceil(totalClasses / itemsPerPage);
    if (currentPage < totalPages) {
        currentPage++;
        loadClasses();
    }
});

// 🔹 Fetch and populate trainers
async function fetchTrainers() {
    try {
        const token = localStorage.getItem("token");
        if (!token) throw new Error("No token");

        const res = await fetch("/api/admin/employees", {
            headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error("Failed to fetch trainers");
        const employees = await res.json();
        // Filter for trainers only
        return employees.filter(emp => emp.role === 'trainer');
    } catch (e) {
        console.error("Error fetching trainers:", e);
        return [];
    }
}

async function populateTrainerDropdown() {
    const trainers = await fetchTrainers();
    const instructorSelect = document.getElementById("instructor");
    instructorSelect.innerHTML = '<option value="">Select a trainer</option>';

    trainers.forEach(trainer => {
        const option = document.createElement("option");
        option.value = trainer.id;
        option.textContent = trainer.name;
        instructorSelect.appendChild(option);
    });
}

// 🔹 Handle new class form submission
document.getElementById("newClassForm").addEventListener("submit", async function (e) {
    e.preventDefault();
    const token = localStorage.getItem("token");
    if (!token) return alert("Please log in first");

    const classData = {
        class_name: document.getElementById("className").value,
        trainer_name: document.getElementById("instructor").value,
        schedule_time: document.getElementById("classDate").value,
        capacity: document.getElementById("classCapacity").value,
    };

    try {
        const res = await fetch("/api/admin/classes", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify(classData),
        });

        if (!res.ok) throw new Error("Failed to create class");

        const tbody = document.querySelector("#classList table tbody");
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${classData.class_name}</td>
            <td>${classData.trainer_name}</td>
            <td>${classData.capacity}</td>
            <td>0</td>
            <td>${classData.capacity}</td>
        `;
        tbody.appendChild(tr);

        document.getElementById("confirmationMessage").style.display = "block";
        setTimeout(() => {
            document.getElementById("confirmationMessage").style.display = "none";
        }, 3000);

        e.target.reset();
    } catch (e) {
        console.error("Error creating class:", e);
        alert("Failed to create class. Please try again.");
    }
});

// 🔹 Handle employee form submission
document.getElementById("newEmployeeForm").addEventListener("submit", function (event) {
    event.preventDefault();
    const employee = {
        employeeName: document.getElementById("employeeName").value,
        employeeRole: document.getElementById("employeeRole").value,
        startDate: document.getElementById("startDate").value,
        status: document.getElementById("status").value,
    };

    const employeeList = document.getElementById("employeeList");
    const li = document.createElement("li");
    li.textContent = `${employee.employeeName}, Role: ${employee.employeeRole}, Start Date: ${employee.startDate}, Status: ${employee.status}`;
    employeeList.appendChild(li);
    event.target.reset();
});

// 🔹 Logout logic
async function logoutUser() {
    try {
        const token = localStorage.getItem("token");
        if (!token) return (window.location.href = "/login");

        await fetch("/api/auth/logout", {
            method: "POST",
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json",
            },
        });
    } catch (error) {
        console.error("Logout failed:", error);
    } finally {
        ["token", "gym_token", "gym_refresh_token", "gym_user"].forEach(k => localStorage.removeItem(k));
        document.cookie = "token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;";
        window.location.href = "/login";
    }
}

function setupLogout() {
    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) logoutBtn.addEventListener("click", logoutUser);
}

async function loadRepairReports() {
    const token = localStorage.getItem("gym_token") || localStorage.getItem("token");
    if (!token) {
        console.error("No token found for fetching repair reports");
        return;
    }

    try {
        const response = await fetch('/api/admin/equipment-reports', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error(`Fetch failed with status ${response.status}: ${errorText}`);
            throw new Error(`Failed to fetch repair reports: ${response.status} ${errorText}`);
        }
        const reports = await response.json();

        const tbody = document.querySelector("#repairReportsTable tbody");
        tbody.innerHTML = '';

        reports.forEach(report => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${report.equipment_name}</td>
                <td>${report.issue_description}</td>
                <td>${report.reporter_name}</td>
                <td>${new Date(report.reported_at).toLocaleString()}</td>
                <td class="repair-status closed">Pending</td>
                <td><button class="repair-action-btn">Mark as In Progress</button></td>
            `;
            tbody.appendChild(tr);
        });

        attachRepairActionHandlers();
    } catch (error) {
        console.error("Error loading repair reports:", error);
    }
}

// Update current month display
function updateCurrentMonth() {
    const now = new Date();
    const month = now.toLocaleString('default', { month: 'long' });
    const year = now.getFullYear();
    document.getElementById('currentMonth').textContent = `Month: ${month} ${year}`;
}

// Load membership data
async function loadMembershipData() {
    try {
        const response = await fetch('/api/admin/membership-stats', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        const data = await response.json();
        
        document.getElementById('newMembers').textContent = data.new_members;
        document.getElementById('renewals').textContent = data.renewals;
        document.getElementById('totalMembers').textContent = data.total_members;
        
        document.getElementById('membershipRevenue').textContent = `$${data.membership_revenue}`;
        document.getElementById('classRevenue').textContent = `$${data.class_revenue}`;
        document.getElementById('merchandiseSales').textContent = `$${data.merchandise_sales}`;
        document.getElementById('totalRevenue').textContent = `$${data.total_revenue}`;
    } catch (error) {
        console.error('Error loading membership data:', error);
    }
}

// Load employees
async function loadEmployees() {
    console.log("Loading employees...");
    const token = localStorage.getItem('token') || localStorage.getItem('gym_token');
    if (!token) {
        console.error("No token found for loading employees");
        return;
    }
    
    try {
        console.log("Fetching employees with token:", token);
        const response = await fetch('/api/admin/employees', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`Fetch failed with status ${response.status}: ${errorText}`);
            throw new Error(`Failed to fetch employees: ${response.status} ${errorText}`);
        }
        
        const employees = await response.json();
        console.log("Fetched employees:", employees);
        
        const tbody = document.querySelector('#employeeTable tbody');
        tbody.innerHTML = '';
        
        employees.forEach(emp => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><input type="radio" name="employeeSelect" value="${emp.id}"></td>
                <td>${emp.name}</td>
                <td>${emp.email}</td>
                <td>${emp.role}</td>
                <td>${emp.tenure || 'N/A'}</td>
            `;
            tbody.appendChild(tr);
        });
        console.log("Employee table updated");
    } catch (error) {
        console.error('Error loading employees:', error);
    }
}

// Load users
async function loadUsers() {
    console.log("Loading users...");
    const token = localStorage.getItem('token') || localStorage.getItem('gym_token');
    if (!token) {
        console.error("No token found for loading users");
        return;
    }
    
    try {
        console.log("Fetching users with token:", token);
        const response = await fetch('/api/admin/users', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`Fetch failed with status ${response.status}: ${errorText}`);
            throw new Error(`Failed to fetch users: ${response.status} ${errorText}`);
        }
        
        const users = await response.json();
        console.log("Fetched users:", users);
        
        const tbody = document.querySelector('#userTable tbody');
        tbody.innerHTML = '';
        
        users.forEach(user => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><input type="radio" name="userSelect" value="${user.id}"></td>
                <td>${user.name}</td>
                <td>${user.email}</td>
                <td>${user.role}</td>
                <td>${user.membership_expiry ? new Date(user.membership_expiry).toLocaleDateString() : 'N/A'}</td>
                <td>${user.auto_payment === 1 ? 'Yes' : 'No'}</td>
            `;
            tbody.appendChild(tr);
        });
        console.log("User table updated");
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

// Initialize dashboard
async function initializeDashboard() {
    console.log("Initializing dashboard components...");
    updateCurrentMonth();
    await loadMembershipData();
    await loadEmployees();
    await loadUsers();
    await loadClasses();
    console.log("Dashboard initialization complete");
    
    // Add direct event listeners to buttons after DOM is fully loaded
    setupButtonEventListeners();
}

// Setup direct event listeners for all buttons
function setupButtonEventListeners() {
    console.log("Setting up button event listeners");
    
    // Get references to all buttons
    const updateRoleBtn = document.getElementById('updateRoleBtn');
    const deleteEmployeeBtn = document.getElementById('deleteEmployeeBtn');
    const updateUserRoleBtn = document.getElementById('updateUserRoleBtn');
    const deleteUserBtn = document.getElementById('deleteUserBtn');
    
    console.log("Buttons found:", 
        updateRoleBtn ? "updateRoleBtn ✓" : "updateRoleBtn ✗", 
        deleteEmployeeBtn ? "deleteEmployeeBtn ✓" : "deleteEmployeeBtn ✗",
        updateUserRoleBtn ? "updateUserRoleBtn ✓" : "updateUserRoleBtn ✗",
        deleteUserBtn ? "deleteUserBtn ✓" : "deleteUserBtn ✗"
    );
    
    // Employee role update button
    if (updateRoleBtn) {
        updateRoleBtn.onclick = function() {
            console.log("Update Role button clicked directly");
            updateEmployeeRole();
        };
    }
    
    // Employee delete button
    if (deleteEmployeeBtn) {
        deleteEmployeeBtn.onclick = function() {
            console.log("Delete Employee button clicked directly");
            deleteEmployee();
        };
    }
    
    // User role update button
    if (updateUserRoleBtn) {
        updateUserRoleBtn.onclick = function() {
            console.log("Update User Role button clicked directly");
            updateUserRole();
        };
    }
    
    // User delete button
    if (deleteUserBtn) {
        deleteUserBtn.onclick = function() {
            console.log("Delete User button clicked directly");
            deleteUser();
        };
    }
}

// Function to update employee role
function updateEmployeeRole() {
    console.log("updateEmployeeRole function called");
    
    // Get selected employee
    const selectedEmployee = document.querySelector('input[name="employeeSelect"]:checked');
    if (!selectedEmployee) {
        alert('Please select an employee first');
        return;
    }
    
    // Get selected role
    const roleSelect = document.getElementById('roleSelect');
    const newRole = roleSelect.value;
    if (!newRole) {
        alert('Please select a new role');
        return;
    }
    
    console.log(`Selected employee ID: ${selectedEmployee.value}, New role: ${newRole}`);
    
    // Get authentication token
    const token = localStorage.getItem('token') || localStorage.getItem('gym_token');
    if (!token) {
        alert('Authentication token not found. Please log in again.');
        window.location.href = '/login';
        return;
    }
    
    // Show a loading message in the UI
    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'loading-message';
    loadingMsg.textContent = 'Updating role...';
    loadingMsg.style.position = 'fixed';
    loadingMsg.style.top = '50%';
    loadingMsg.style.left = '50%';
    loadingMsg.style.transform = 'translate(-50%, -50%)';
    loadingMsg.style.backgroundColor = '#f8f9fa';
    loadingMsg.style.padding = '20px';
    loadingMsg.style.borderRadius = '5px';
    loadingMsg.style.boxShadow = '0 0 10px rgba(0,0,0,0.2)';
    loadingMsg.style.zIndex = '9999';
    document.body.appendChild(loadingMsg);
    
    // Use fetch with async/await pattern for better performance
    fetch(`/api/admin/employees/${selectedEmployee.value}/role`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ role: newRole })
    })
    .then(response => response.json())
    .then(data => {
        // Remove loading message
        document.body.removeChild(loadingMsg);
        
        if (data.message) {
            alert(`Role updated successfully from ${data.old_role} to ${data.new_role}`);
            window.location.reload();
        } else {
            throw new Error(data.error || 'Failed to update role');
        }
    })
    .catch(error => {
        // Remove loading message
        if (document.body.contains(loadingMsg)) {
            document.body.removeChild(loadingMsg);
        }
        
        console.error('Error during fetch:', error);
        alert('Error updating role: ' + error.message);
    });
}

// Function to delete employee
function deleteEmployee() {
    console.log("deleteEmployee function called");
    
    // Get selected employee
    const selectedEmployee = document.querySelector('input[name="employeeSelect"]:checked');
    if (!selectedEmployee) {
        alert('Please select an employee first');
        return;
    }
    
    // Confirm deletion
    if (!confirm('Are you sure you want to delete this employee?')) {
        return;
    }
    
    // Get authentication token
    const token = localStorage.getItem('token') || localStorage.getItem('gym_token');
    if (!token) {
        alert('Authentication token not found. Please log in again.');
        window.location.href = '/login';
        return;
    }
    
    // Show a loading message in the UI
    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'loading-message';
    loadingMsg.textContent = 'Deleting employee...';
    loadingMsg.style.position = 'fixed';
    loadingMsg.style.top = '50%';
    loadingMsg.style.left = '50%';
    loadingMsg.style.transform = 'translate(-50%, -50%)';
    loadingMsg.style.backgroundColor = '#f8f9fa';
    loadingMsg.style.padding = '20px';
    loadingMsg.style.borderRadius = '5px';
    loadingMsg.style.boxShadow = '0 0 10px rgba(0,0,0,0.2)';
    loadingMsg.style.zIndex = '9999';
    document.body.appendChild(loadingMsg);
    
    // Use fetch with async/await pattern for better performance
    fetch(`/api/admin/employees/${selectedEmployee.value}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => response.json())
    .then(data => {
        // Remove loading message
        document.body.removeChild(loadingMsg);
        
        if (data.message) {
            alert('Employee deleted successfully');
            window.location.reload();
        } else {
            throw new Error(data.error || 'Failed to delete employee');
        }
    })
    .catch(error => {
        // Remove loading message
        if (document.body.contains(loadingMsg)) {
            document.body.removeChild(loadingMsg);
        }
        
        console.error('Error during fetch:', error);
        alert('Error deleting employee: ' + error.message);
    });
}

// Function to update user role
function updateUserRole() {
    console.log("updateUserRole function called");
    
    // Get selected user
    const selectedUser = document.querySelector('input[name="userSelect"]:checked');
    if (!selectedUser) {
        alert('Please select a user first');
        return;
    }
    
    // Get selected role
    const roleSelect = document.getElementById('userRoleSelect');
    const newRole = roleSelect.value;
    if (!newRole) {
        alert('Please select a new role');
        return;
    }
    
    console.log(`Selected user ID: ${selectedUser.value}, New role: ${newRole}`);
    
    // Get authentication token
    const token = localStorage.getItem('token') || localStorage.getItem('gym_token');
    if (!token) {
        alert('Authentication token not found. Please log in again.');
        window.location.href = '/login';
        return;
    }
    
    // Show a loading message in the UI
    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'loading-message';
    loadingMsg.textContent = 'Updating role...';
    loadingMsg.style.position = 'fixed';
    loadingMsg.style.top = '50%';
    loadingMsg.style.left = '50%';
    loadingMsg.style.transform = 'translate(-50%, -50%)';
    loadingMsg.style.backgroundColor = '#f8f9fa';
    loadingMsg.style.padding = '20px';
    loadingMsg.style.borderRadius = '5px';
    loadingMsg.style.boxShadow = '0 0 10px rgba(0,0,0,0.2)';
    loadingMsg.style.zIndex = '9999';
    document.body.appendChild(loadingMsg);
    
    // Use fetch with async/await pattern for better performance
    fetch(`/api/admin/users/${selectedUser.value}/role`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ role: newRole })
    })
    .then(response => response.json())
    .then(data => {
        // Remove loading message
        document.body.removeChild(loadingMsg);
        
        if (data.message) {
            alert(`Role updated successfully from ${data.old_role} to ${data.new_role}`);
            window.location.reload();
        } else {
            throw new Error(data.error || 'Failed to update role');
        }
    })
    .catch(error => {
        // Remove loading message
        if (document.body.contains(loadingMsg)) {
            document.body.removeChild(loadingMsg);
        }
        
        console.error('Error during fetch:', error);
        alert('Error updating role: ' + error.message);
    });
}

// Function to delete user
function deleteUser() {
    console.log("deleteUser function called");
    
    // Get selected user
    const selectedUser = document.querySelector('input[name="userSelect"]:checked');
    if (!selectedUser) {
        alert('Please select a user first');
        return;
    }
    
    // Confirm deletion
    if (!confirm('Are you sure you want to delete this user?')) {
        return;
    }
    
    // Get authentication token
    const token = localStorage.getItem('token') || localStorage.getItem('gym_token');
    if (!token) {
        alert('Authentication token not found. Please log in again.');
        window.location.href = '/login';
        return;
    }
    
    // Show a loading message in the UI
    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'loading-message';
    loadingMsg.textContent = 'Deleting user...';
    loadingMsg.style.position = 'fixed';
    loadingMsg.style.top = '50%';
    loadingMsg.style.left = '50%';
    loadingMsg.style.transform = 'translate(-50%, -50%)';
    loadingMsg.style.backgroundColor = '#f8f9fa';
    loadingMsg.style.padding = '20px';
    loadingMsg.style.borderRadius = '5px';
    loadingMsg.style.boxShadow = '0 0 10px rgba(0,0,0,0.2)';
    loadingMsg.style.zIndex = '9999';
    document.body.appendChild(loadingMsg);
    
    // Use fetch with async/await pattern for better performance
    fetch(`/api/admin/users/${selectedUser.value}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => response.json())
    .then(data => {
        // Remove loading message
        document.body.removeChild(loadingMsg);
        
        if (data.message) {
            alert('User deleted successfully');
            window.location.reload();
        } else {
            throw new Error(data.error || 'Failed to delete user');
        }
    })
    .catch(error => {
        // Remove loading message
        if (document.body.contains(loadingMsg)) {
            document.body.removeChild(loadingMsg);
        }
        
        console.error('Error during fetch:', error);
        alert('Error deleting user: ' + error.message);
    });
}


