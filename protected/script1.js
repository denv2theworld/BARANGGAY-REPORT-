const API_BASE_URL = "https://baranggay-report.onrender.com";

const reportsList = document.getElementById('reportsList');
const pendingCount = document.getElementById('pendingCount');
const processingCount = document.getElementById('processingCount');
const finishedCount = document.getElementById('finishedCount');

async function loadReports() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/reports`, {
            credentials: 'include',
        });

        if (response.status === 401) {
            window.location.href = '/admin.html';
            return;
        }

        if (!response.ok) {
            throw new Error('Could not load reports.');
        }

        const reports = await response.json();
        renderReports(reports);
        renderCounts(reports);

    } catch (error) {
        reportsList.textContent = `Error: ${error.message}`;
    }
}

function renderCounts(reports) {
    pendingCount.textContent = reports.filter(r => r.status === 'pending').length;
    processingCount.textContent = reports.filter(r => r.status === 'processing').length;
    finishedCount.textContent = reports.filter(r => r.status === 'finished').length;
}

function renderReports(reports) {
    reportsList.innerHTML = '';

    if (reports.length === 0) {
        reportsList.textContent = 'No reports yet.';
        return;
    }

    reports.forEach(report => {
        const card = document.createElement('div');
        card.className = 'report-card';

        card.innerHTML = `
            <h4>${escapeHtml(report.name)}</h4>
            <p><strong>Mobile:</strong> ${escapeHtml(report.mobile)}</p>
            <p><strong>Location:</strong> ${escapeHtml(report.location)}</p>
            <p><strong>Address:</strong> ${escapeHtml(report.address)}</p>
            <p><strong>Description:</strong> ${escapeHtml(report.description)}</p>
            <p><strong>Status:</strong> <span class="status-badge ${report.status}">${report.status}</span></p>
            <p><strong>Submitted:</strong> ${new Date(report.created_at).toLocaleString()}</p>
            <label>
                Update status:
                <select data-id="${report.id}" class="status-select">
                    <option value="pending" ${report.status === 'pending' ? 'selected' : ''}>Pending</option>
                    <option value="processing" ${report.status === 'processing' ? 'selected' : ''}>Processing</option>
                    <option value="finished" ${report.status === 'finished' ? 'selected' : ''}>Finished</option>
                </select>
            </label>
        `;

        reportsList.appendChild(card);
    });

    document.querySelectorAll('.status-select').forEach(select => {
        select.addEventListener('change', async (event) => {
            const id = event.target.dataset.id;
            const newStatus = event.target.value;
            await updateStatus(id, newStatus);
        });
    });
}

async function updateStatus(id, status) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/reports/${id}/status`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ status }),
        });

        if (!response.ok) {
            throw new Error('Could not update status.');
        }

        loadReports();

    } catch (error) {
        alert(error.message);
    }
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

loadReports();
