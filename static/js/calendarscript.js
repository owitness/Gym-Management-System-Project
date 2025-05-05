document.addEventListener('DOMContentLoaded', async () => {
    const calendarContainer = document.getElementById("calendar");
    const trainerFilter = document.getElementById("trainer-filter");
    const classFilter = document.getElementById("class-filter");
    const monthHeader = document.getElementById("month-header");
    const prevBtn = document.getElementById("prev-month");
    const nextBtn = document.getElementById("next-month");

    let currentDate = new Date();
    let allClasses = [];

    async function fetchClasses() {
        let token = localStorage.getItem("token");
        if (!token) {
            const urlParams = new URLSearchParams(window.location.search);
            token = urlParams.get('token');
            if (token) localStorage.setItem("token", token);
        }
        if (!token) return [];

        try {
            const response = await fetch('/api/classes', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            if (!response.ok) return [];
            return await response.json();
        } catch {
            return [];
        }
    }

    function renderCalendar(classData) {
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth();
        const firstDay = new Date(year, month, 1).getDay();
        const totalDays = new Date(year, month + 1, 0).getDate();
        const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

        calendarContainer.innerHTML = '';
        monthHeader.textContent = `${currentDate.toLocaleString('default', { month: 'long' })} ${year}`;

        weekdays.forEach(day => {
            const header = document.createElement('div');
            header.classList.add('weekday');
            header.textContent = day;
            calendarContainer.appendChild(header);
        });

        for (let i = 0; i < firstDay; i++) {
            const empty = document.createElement('div');
            empty.classList.add('empty');
            calendarContainer.appendChild(empty);
        }

        for (let day = 1; day <= totalDays; day++) {
            const dateString = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const dayBox = document.createElement('div');
            dayBox.classList.add('day');
            dayBox.innerHTML = `<strong>${day}</strong>`;

            const classesToday = classData.filter(cls => {
                const classDate = new Date(cls.schedule_time);
                const formattedDate = `${classDate.getFullYear()}-${String(classDate.getMonth() + 1).padStart(2, '0')}-${String(classDate.getDate()).padStart(2, '0')}`;
                return formattedDate === dateString;
            });

            if (classesToday.length > 0) {
                const dot = document.createElement('div');
                dot.classList.add('dot');
                dayBox.appendChild(dot);

                dayBox.addEventListener('click', () => showClassesForDay(dateString, classesToday));
            }

            calendarContainer.appendChild(dayBox);
        }
    }

    function populateFilters(classes) {
        const trainers = [...new Set(classes.map(c => c.trainer_name))];
        const types = [...new Set(classes.map(c => c.class_name))];

        trainers.forEach(name => {
            const opt = document.createElement('option');
            opt.value = name;
            opt.textContent = name;
            trainerFilter.appendChild(opt);
        });

        types.forEach(name => {
            const opt = document.createElement('option');
            opt.value = name;
            opt.textContent = name;
            classFilter.appendChild(opt);
        });
    }

    function filterClasses() {
        const trainer = trainerFilter.value;
        const type = classFilter.value;

        return allClasses.filter(cls =>
            (!trainer || cls.trainer_name === trainer) &&
            (!type || cls.class_name === type)
        );
    }

    allClasses = await fetchClasses();
    renderCalendar(allClasses);
    populateFilters(allClasses);

    [trainerFilter, classFilter].forEach(filter => {
        filter.addEventListener('change', () => {
            renderCalendar(filterClasses());
        });
    });

    prevBtn.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        renderCalendar(filterClasses());
    });

    nextBtn.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        renderCalendar(filterClasses());
    });
});

// For booking class from modal
window.bookClass = async (classId, button) => {
    let token = localStorage.getItem('token');
    if (!token) {
        const urlParams = new URLSearchParams(window.location.search);
        token = urlParams.get('token');
        if (token) localStorage.setItem("token", token);
    }
    if (!token) {
        showError("Please sign in first.");
        return;
    }

    // Disable button and show loading state
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = "Booking...";

    try {
        const res = await fetch(`/api/classes/${classId}/book`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        const data = await res.json();

        if (res.ok) {
            showSuccess("Class booked successfully!");
            // Refresh the class list after 1.5 seconds
            setTimeout(() => {
                const currentDate = document.getElementById("modal-date").textContent;
                const date = new Date(currentDate);
                const dateString = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
                fetchClasses().then(classes => {
                    const classesForDay = classes.filter(cls => {
                        const classDate = new Date(cls.schedule_time);
                        const formattedDate = `${classDate.getFullYear()}-${String(classDate.getMonth() + 1).padStart(2, '0')}-${String(classDate.getDate()).padStart(2, '0')}`;
                        return formattedDate === dateString;
                    });
                    showClassesForDay(dateString, classesForDay);
                });
            }, 1500);
        } else {
            showError(data.error || "Booking failed due to an unexpected error.");
            // Reset button state
            button.disabled = false;
            button.textContent = originalText;
        }
    } catch (error) {
        showError("Booking failed. Please check your connection or try again later.");
        // Reset button state
        button.disabled = false;
        button.textContent = originalText;
    }
};

function showSuccess(message) {
    const successDiv = document.getElementById("success-message");
    const errorDiv = document.getElementById("error-message");
    successDiv.textContent = message;
    successDiv.style.display = "block";
    errorDiv.style.display = "none";
    setTimeout(() => {
        successDiv.style.display = "none";
    }, 3000);
}

function showError(message) {
    const successDiv = document.getElementById("success-message");
    const errorDiv = document.getElementById("error-message");
    errorDiv.textContent = message;
    errorDiv.style.display = "block";
    successDiv.style.display = "none";
    setTimeout(() => {
        errorDiv.style.display = "none";
    }, 3000);
}

// For modal display of day classes
function showClassesForDay(date, classes) {
    document.getElementById("modal-date").textContent = new Date(date).toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });

    const list = document.getElementById("modal-class-list");
    list.innerHTML = '';

    if (classes.length === 0) {
        list.innerHTML = '<p>No classes scheduled for this day.</p>';
        return;
    }

    classes.forEach(cls => {
        const div = document.createElement("div");
        div.classList.add("class-item");

        // Add 4 hours to the class time
        const classTime = new Date(cls.schedule_time);
        classTime.setHours(classTime.getHours() + 4);
        
        const time = classTime.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });

        const isFull = cls.current_bookings >= cls.capacity;
        const spotsLeft = cls.capacity - cls.current_bookings;

        div.innerHTML = `
            <h3>${cls.class_name}</h3>
            <p><strong>Time:</strong> ${time}</p>
            <p><strong>Trainer:</strong> ${cls.trainer_name}</p>
            <p><strong>Spots Available:</strong> ${spotsLeft} of ${cls.capacity}</p>
            ${cls.description ? `<p><strong>Description:</strong> ${cls.description}</p>` : ''}
            <button onclick="bookClass(${cls.id}, this)"
                ${isFull ? 'disabled' : ''}>
                ${isFull ? 'Class Full' : 'Book Class'}
            </button>
        `;
        list.appendChild(div);
    });

    document.getElementById("class-modal").style.display = "block";
}

function closeClassModal() {
    document.getElementById("class-modal").style.display = "none";
}

// For dashboard link to calendar
function navigateToCalendar() {
    const token = localStorage.getItem('token');
    if (!token) {
        alert("Please sign in first.");
        window.location.href = '/login';
        return;
    }
    window.location.href = `/calendar?token=${encodeURIComponent(token)}`;
}
