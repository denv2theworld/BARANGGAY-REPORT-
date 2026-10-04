// 1. Select DOM elements
const enrollmentForm = document.getElementById('enrollmentForm');
const successCard = document.getElementById('successCard');
const resetBtn = document.getElementById('resetBtn');

// Summary field references
const summaryName = document.getElementById('summaryName');
const summaryMobile = document.getElementById('summaryMobile');
const summaryLocation = document.getElementById('summaryLocation');
const summaryDesc = document.getElementById('summaryDesc');

// 2. Form submission handler
enrollmentForm.addEventListener('submit', function(event) {
    // Prevent page reload
    event.preventDefault();

    // Capture values from input fields
    const nameVal = document.getElementById('name').value;
    const mobileVal = document.getElementById('mobilenumber').value;
    const locationVal = document.getElementById('location').value;
    const descVal = document.getElementById('description').value;

    // Display captured details on the success summary card
    summaryName.textContent = nameVal;
    summaryMobile.textContent = mobileVal;
    summaryLocation.textContent = locationVal;
    summaryDesc.textContent = descVal;

    // Hide the form and show the success card
    enrollmentForm.classList.add('hidden');
    successCard.classList.remove('hidden');

    // Reset input fields
    enrollmentForm.reset();
});

// 3. Reset button to submit a new report
resetBtn.addEventListener('click', function() {
    successCard.classList.add('hidden');
    enrollmentForm.classList.remove('hidden');
});