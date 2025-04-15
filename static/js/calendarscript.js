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
window.bookClass = async (classId) => {
    let token = localStorage.getItem('token');
    if (!token) {
        const urlParams = new URLSearchParams(window.location.search);
        token = urlParams.get('token');
        if (token) localStorage.setItem("token", token);
    }
    if (!token) {
        alert("Please sign in first.");
        return;
    }

    try {
        const res = await fetch(`/api/classes/${classId}/book`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.ok) {
            alert("Class booked!");
        } else {
            const err = await res.json().catch(() => null);
            alert(err?.error || "Booking failed due to an unexpected error.");
        }
    } catch {
        alert("Booking failed. Please check your connection or try again later.");
    }
};

// For modal display of day classes
function showClassesForDay(date, classes) {
    document.getElementById("modal-date").textContent = new Date(date).toDateString();

    const list = document.getElementById("modal-class-list");
    list.innerHTML = '';

    classes.forEach(cls => {
        const div = document.createElement("div");
        div.classList.add("class-item");

        const time = new Date(cls.schedule_time).toLocaleTimeString('en-US', {
            hour: '2-digit', minute: '2-digit'
        });

        div.innerHTML = `
            <h3>${cls.class_name}</h3>
            <p>Time: ${time}</p>
            <p>Trainer: ${cls.trainer_name}</p>
            <p>Available: ${cls.capacity - cls.current_bookings}</p>
            <button onclick="bookClass(${cls.id})"
                ${cls.current_bookings >= cls.capacity ? 'disabled' : ''}>
                ${cls.current_bookings >= cls.capacity ? 'Full' : 'Book'}
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
