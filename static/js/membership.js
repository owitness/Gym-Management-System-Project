let currentPage = 0;

function showPage(index) {
    document.querySelectorAll('.form-page').forEach((page, i) => {
        page.classList.toggle('active', i === index);
    });
    currentPage = index;
    if (index === 3) updateConfirmation();
}

function validateAndNext(nextIndex) {
    const inputs = document.querySelectorAll(`#page${currentPage + 1} input[required]`);
    let valid = true;
    inputs.forEach(input => {
        if (!input.checkValidity()) {
            input.reportValidity();
            valid = false;
        }
    });
    if (valid) showPage(nextIndex);
}

function updateConfirmation() {
    const getVal = id => document.getElementById(id)?.value || '';
    const setText = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };

    setText("confirmName", `${getVal("fname")} ${getVal("lname")}`);
    setText("confirmEmail", getVal("email"));
    setText("confirmCardnumber", "*".repeat(12) + getVal("cardnumber").slice(-4));
    setText("confirmExpiration", getVal("expiration"));
    setText("confirmCardholder", getVal("cardholdername"));
    setText("confirmStreetaddress", getVal("streetaddress"));
    setText("confirmCity", getVal("city"));
    setText("confirmState", getVal("state"));
    setText("confirmZipcode", getVal("zipcode"));
}

document.addEventListener('DOMContentLoaded', () => {
    const nextBtns = document.querySelectorAll('.next');
    const prevBtns = document.querySelectorAll('.previous');
    const submitBtn = document.getElementById('submitBtn');
    const expirationInput = document.getElementById('expiration');

    nextBtns.forEach((btn, i) => {
        btn.addEventListener('click', () => validateAndNext(currentPage + 1));
    });

    prevBtns.forEach((btn, i) => {
        btn.addEventListener('click', () => showPage(currentPage - 1));
    });

    if (submitBtn) {
        submitBtn.addEventListener('click', () => {
            const membership = window.membershipType || 'monthly';
            submitForm(membership);
        });
    }

    if (expirationInput) {
        expirationInput.addEventListener('input', e => {
            let val = e.target.value.replace(/\D/g, '');
            if (val.length > 2) val = val.slice(0, 2) + '/' + val.slice(2, 4);
            e.target.value = val;
        });
    }

    document.getElementById('registration')?.addEventListener('submit', e => e.preventDefault());
});
