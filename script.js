// 0. Point this at your running backend.
const API_BASE_URL = "https://baranggay-report.onrender.com";

// 1. Select DOM elements
const enrollmentForm = document.getElementById('enrollmentForm');
const successCard = document.getElementById('successCard');
const resetBtn = document.getElementById('resetBtn');
const submitBtn = document.getElementById('submitBtn');

// Summary field references
const summaryName = document.getElementById('summaryName');
const summaryMobile = document.getElementById('summaryMobile');
const summaryLocation = document.getElementById('summaryLocation');
const summaryDesc = document.getElementById('summaryDesc');

// 2. Form submission handler
enrollmentForm.addEventListener('submit', async function(event) {
    event.preventDefault();

    const nameVal = document.getElementById('name').value;
    const mobileVal = document.getElementById('mobilenumber').value;
    const locationVal = document.getElementById('location').value;
    const addressVal = document.getElementById('address').value;
    const descVal = document.getElementById('description').value;

    submitBtn.disabled = true;
    submitBtn.textContent = "Submitting...";

    try {
        const response = await fetch(`${API_BASE_URL}/api/reports`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                name: nameVal,
                mobile: mobileVal,
                location: locationVal,
                address: addressVal,
                description: descVal,
            }),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const message = errorData.errors
                ? Object.values(errorData.errors).join(' ')
                : (errorData.error || 'Something went wrong. Please try again.');
            throw new Error(message);
        }

        // Backend only returns {id, status} on success, not the full record,
        // so we show back what the user typed in.
        summaryName.textContent = nameVal;
        summaryMobile.textContent = mobileVal;
        summaryLocation.textContent = locationVal;
        summaryDesc.textContent = descVal;

        enrollmentForm.classList.add('hidden');
        successCard.classList.remove('hidden');
        enrollmentForm.reset();

    } catch (error) {
        alert(`Report could not be submitted: ${error.message}`);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Submit Report";
    }
});

// 3. Reset button to submit a new report
resetBtn.addEventListener('click', function() {
    successCard.classList.add('hidden');
    enrollmentForm.classList.remove('hidden');
});
