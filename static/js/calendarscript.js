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
        const token = localStorage.getItem("token");
        if (!token) {
            console.warn("No token found in localStorage.");
            return [];
        }

        try {
            const response = await fetch('/api/classes', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                const error = await response.json();
                console.error("Failed to fetch classes:", error);
                return [];
            }

            return await response.json();
        } catch (error) {
            console.error("Error fetching classes:", error);
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
            const emptySlot = document.createElement('div');
            emptySlot.classList.add('empty');
            calendarContainer.appendChild(emptySlot);
        }

        for (let day = 1; day <= totalDays; day++) {
            const dateString = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const dayBox = document.createElement('div');
            dayBox.classList.add('day');
            dayBox.innerHTML = `<strong>${day}</strong><div class="class-list"></div>`;

            const classList = dayBox.querySelector('.class-list');
            const classesToday = classData.filter(cls => {
                const classDate = new Date(cls.schedule_time);
                const formattedDate = `${classDate.getFullYear()}-${String(classDate.getMonth() + 1).padStart(2, '0')}-${String(classDate.getDate()).padStart(2, '0')}`;
                return formattedDate === dateString;
            });

            if (classesToday.length > 0) {
                dayBox.classList.add('has-classes');
                const summary = document.createElement('small');
                summary.textContent = `${classesToday.length} class${classesToday.length > 1 ? 'es' : ''}`;
                dayBox.insertBefore(summary, classList);
            }

            classesToday.forEach(cls => {
                const div = document.createElement('div');
                div.classList.add('class-item');
                div.innerHTML = `
                    <span>${cls.class_name}</span><br/>
                    <small>${new Date(cls.schedule_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</small><br/>
                    <em>${cls.trainer_name}</em><br/>
                    <button onclick="bookClass(${cls.id})"
                        ${cls.current_bookings >= cls.capacity ? 'disabled' : ''}>
                        ${cls.current_bookings >= cls.capacity ? 'Full' : 'Book'}
                    </button>
                `;
                classList.appendChild(div);
            });

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

    // Initial load
    allClasses = await fetchClasses();
    renderCalendar(allClasses);
    populateFilters(allClasses);

    [trainerFilter, classFilter].forEach(filter => {
        filter.addEventListener('change', () => {
            const trainer = trainerFilter.value;
            const type = classFilter.value;

            const filtered = allClasses.filter(cls =>
                (!trainer || cls.trainer_name === trainer) &&
                (!type || cls.class_name === type)
            );

            renderCalendar(filtered);
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

    function filterClasses() {
        const trainer = trainerFilter.value;
        const type = classFilter.value;

        return allClasses.filter(cls =>
            (!trainer || cls.trainer_name === trainer) &&
            (!type || cls.class_name === type)
        );
    }
});

// Moved to global scope so onclick="bookClass(...)" works in HTML
window.bookClass = async (classId) => {
    const token = localStorage.getItem('token');
    if (!token) return alert("Please sign in first.");

    try {
        const res = await fetch(`/api/classes/${classId}/book`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.ok) {
            alert("Class booked!");
        } else {
            const err = await res.json().catch(() => null);
            if (err && err.error) {
                alert(err.error);
            } else {
                alert("Booking failed due to an unexpected error.");
            }
        }
    } catch (error) {
        console.error("Booking error:", error);
        alert("Booking failed. Please check your connection or try again later.");
    }
};
