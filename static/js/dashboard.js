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

      // Update the DOM
      document.getElementById('username').textContent = membership?.member_name || "Member";
      document.getElementById('membstatus').textContent = membership?.status || "N/A";
      document.getElementById('membtype').textContent = membership?.membership_type || "N/A";
    } catch (error) {
      console.error('Error loading dashboard:', error);
      alert('Could not load dashboard information.');
    }
  }

function logout() {
    localStorage.clear();
    sessionStorage.clear();
    window.location.href="/home";
}