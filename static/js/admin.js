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
    initRepairOrderButtons();
    loadClasses();
    populateTrainerDropdown();
    setupLogout();
    loadRepairReports();
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

async function loadClasses() {
    const classes = await fetchClasses();
    const tbody = document.querySelector("#classList table tbody");
    tbody.innerHTML = "";

    classes.forEach(cls => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${cls.class_name}</td>
            <td>${cls.trainer_name}</td>
            <td>${cls.capacity}</td>
            <td>${cls.current_bookings}</td>
            <td>${cls.capacity - cls.current_bookings}</td>
        `;
        tbody.appendChild(tr);
    });
}

// 🔹 Fetch and populate trainers
async function fetchTrainers() {
    try {
        const token = localStorage.getItem("token");
        if (!token) throw new Error("No token");

        const res = await fetch("/api/admin/trainers", {
            headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error("Failed to fetch trainers");
        return await res.json();
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


