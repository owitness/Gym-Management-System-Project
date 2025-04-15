document.addEventListener('DOMContentLoaded', () => {
    const checkInBtn = document.getElementById('check-in-btn');
    const checkOutBtn = document.getElementById('check-out-btn');
    const dateRange = document.getElementById('date-range');

    const urlParams = new URLSearchParams(window.location.search);
    const tokenFromURL = urlParams.get('token');
    if (tokenFromURL) {
        localStorage.setItem('token', tokenFromURL);
        window.history.replaceState({}, document.title, "/attendance");
    }

    if (checkInBtn) checkInBtn.onclick = checkIn;
    if (checkOutBtn) checkOutBtn.onclick = checkOut;
    if (dateRange) dateRange.onchange = loadAttendanceHistory;

    loadCurrentStatus();
    loadAttendanceHistory();
    setInterval(loadCurrentStatus, 60000);
});

async function loadCurrentStatus() {
    try {
        const res = await fetch('/api/attendance/current', {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        const status = await res.json();
        const statusDiv = document.getElementById('current-status');
        const checkInBtn = document.getElementById('check-in-btn');
        const checkOutBtn = document.getElementById('check-out-btn');

        if (status.checked_in) {
            statusDiv.innerHTML = `
                <div class="status-item checked-in">
                    <h3>Currently Checked In</h3>
                    <p>Since: ${new Date(status.check_in_time).toLocaleString()}</p>
                    <p>Duration: ${calculateDuration(status.check_in_time)}</p>
                </div>
            `;
            checkInBtn.style.display = 'none';
            checkOutBtn.style.display = 'block';
        } else {
            statusDiv.innerHTML = `
                <div class="status-item">
                    <h3>Not Checked In</h3>
                    <p>Last visit: ${status.last_visit ? new Date(status.last_visit).toLocaleString() : 'No previous visits'}</p>
                </div>
            `;
            checkInBtn.style.display = 'block';
            checkOutBtn.style.display = 'none';
        }
    } catch (err) {
        console.error('Error loading current status:', err);
    }
}

async function loadAttendanceHistory() {
    const days = document.getElementById('date-range').value;
    try {
        const res = await fetch(`/api/attendance/history?days=${days}`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        const history = await res.json();
        const historyDiv = document.getElementById('attendance-history');
        if (!Array.isArray(history) || history.length === 0) {
            historyDiv.innerHTML = '<p>No attendance records found</p>';
            return;
        }
        historyDiv.innerHTML = history.map(visit => `
            <div class="attendance-item">
                <h3>${new Date(visit.check_in_time).toLocaleDateString()}</h3>
                <p>Check-in: ${new Date(visit.check_in_time).toLocaleTimeString()}</p>
                ${visit.check_out_time ?
                    `<p>Check-out: ${new Date(visit.check_out_time).toLocaleTimeString()}</p>
                     <p>Duration: ${calculateDuration(visit.check_in_time, visit.check_out_time)}</p>` :
                    '<p>No check-out recorded</p>'
                }
            </div>
        `).join('');
        loadStatistics(history);
    } catch (err) {
        console.error('Error loading attendance history:', err);
    }
}

function loadStatistics(history) {
    const stats = {
        totalVisits: history.length,
        averageDuration: 0,
        longestVisit: 0,
        mostFrequentDay: ''
    };

    const dayCount = {};
    let totalDuration = 0;

    history.forEach(visit => {
        const day = new Date(visit.check_in_time).toLocaleDateString('en-US', { weekday: 'long' });
        dayCount[day] = (dayCount[day] || 0) + 1;

        if (visit.check_out_time) {
            const duration = new Date(visit.check_out_time) - new Date(visit.check_in_time);
            totalDuration += duration;
            stats.longestVisit = Math.max(stats.longestVisit, duration);
        }
    });

    stats.averageDuration = totalDuration / history.length;
    stats.mostFrequentDay = Object.entries(dayCount).sort((a, b) => b[1] - a[1])[0]?.[0] || 'N/A';

    document.getElementById('attendance-stats').innerHTML = `
        <div class="stats-item">
            <p>Total Visits: ${stats.totalVisits}</p>
            <p>Average Duration: ${formatDuration(stats.averageDuration)}</p>
            <p>Longest Visit: ${formatDuration(stats.longestVisit)}</p>
            <p>Most Frequent Day: ${stats.mostFrequentDay}</p>
        </div>
    `;
}

async function checkIn() {
    try {
        const res = await fetch('/api/attendance/check-in', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        if (res.ok) {
            loadCurrentStatus();
            loadAttendanceHistory();
        } else {
            const err = await res.json();
            alert(err.error);
        }
    } catch (err) {
        console.error('Check-in failed:', err);
    }
}

async function checkOut() {
    try {
        const res = await fetch('/api/attendance/check-out', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        if (res.ok) {
            loadCurrentStatus();
            loadAttendanceHistory();
        } else {
            const err = await res.json();
            alert(err.error);
        }
    } catch (err) {
        console.error('Check-out failed:', err);
    }
}

function calculateDuration(start, end = new Date()) {
    const duration = new Date(end) - new Date(start);
    return formatDuration(duration);
}

function formatDuration(ms) {
    if (!ms || isNaN(ms)) return 'N/A';
    const hours = Math.floor(ms / (1000 * 60 * 60));
    const minutes = Math.floor((ms % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours}h ${minutes}m`;
}

function logout() {
    localStorage.removeItem('token');
    window.location.href = '/login';
}