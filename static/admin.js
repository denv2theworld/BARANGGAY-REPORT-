const API_BASE_URL = "https://baranggay-report.onrender.com";

const passwordForm = document.getElementById('passwordForm');
const loginBtn = document.getElementById('logginginBtn');
const loginError = document.getElementById('loginError');

passwordForm.addEventListener('submit', async function (event) {
    event.preventDefault();

    const password = document.getElementById('password').value;

    loginBtn.disabled = true;
    loginBtn.textContent = "Logging in...";
    loginError.classList.add('hidden');

    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ password }),
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(data.error || 'Login failed. Please try again.');
        }

        window.location.href = '/portal.html';

    } catch (error) {
        loginError.textContent = error.message;
        loginError.classList.remove('hidden');
    } finally {
        loginBtn.disabled = false;
        loginBtn.textContent = "Log in";
    }
});
