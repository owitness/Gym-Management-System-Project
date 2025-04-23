let currentPage = 1;
const totalPages = 4;

function showPage(pageNum) {
    if (pageNum < 1 || pageNum > totalPages) return;
    
    document.querySelectorAll('.form-page').forEach(page => {
        page.classList.remove('active');
    });
    
    document.getElementById(`page${pageNum}`).classList.add('active');
    currentPage = pageNum;
}

function validateInputs(pageNum) {
    const page = document.getElementById(`page${pageNum}`);
    const inputs = page.querySelectorAll('input[required]');
    
    for (const input of inputs) {
        if (!input.value) {
            alert(`Please fill in ${input.placeholder || 'this field'}`);
            input.focus();
            return false;
        }
        
        if (input.pattern && !new RegExp(input.pattern).test(input.value)) {
            alert(`Invalid format for ${input.placeholder || 'this field'}`);
            input.focus();
            return false;
        }
    }
    
    return true;
}

function validateAndNext(nextPage) {
    if (validateInputs(currentPage)) {
        if (currentPage === 1) {
            document.getElementById('confirmName').textContent = 
                `${document.getElementById('fname').value} ${document.getElementById('lname').value}`;
            document.getElementById('confirmEmail').textContent = 
                document.getElementById('email').value;
        } else if (currentPage === 2) {
            const cardNumber = document.getElementById('cardnumber').value;
            document.getElementById('confirmCardnumber').textContent = 
                `**** **** **** ${cardNumber.slice(-4)}`;
            document.getElementById('confirmExpiration').textContent = 
                document.getElementById('expiration').value;
            document.getElementById('confirmCardholder').textContent = 
                document.getElementById('cardholdername').value;
        } else if (currentPage === 3) {
            document.getElementById('confirmStreetaddress').textContent = 
                document.getElementById('streetaddress').value;
            document.getElementById('confirmCity').textContent = 
                document.getElementById('city').value;
            document.getElementById('confirmState').textContent = 
                document.getElementById('state').value;
            document.getElementById('confirmZipcode').textContent = 
                document.getElementById('zipcode').value;
        }
        showPage(nextPage);
    }
}

async function submitForm(membershipType) {
    try {
        // Determine membership type from URL if not provided
        if (!membershipType) {
            const path = window.location.pathname;
            if (path.includes('/monthly')) {
                membershipType = 'monthly';
            } else if (path.includes('/annual')) {
                membershipType = 'annual';
            } else if (path.includes('/student')) {
                membershipType = 'student';
            } else {
                membershipType = 'monthly'; // Default to monthly
            }
        }
        
        const formData = {
            name: `${document.getElementById('fname').value} ${document.getElementById('lname').value}`,
            email: document.getElementById('email').value,
            password: document.getElementById('password').value,
            dob: document.getElementById('dob').value,
            card_number: document.getElementById('cardnumber').value,
            exp: document.getElementById('expiration').value,
            cvv: document.getElementById('securitycode').value,
            card_holder_name: document.getElementById('cardholdername').value,
            address: document.getElementById('streetaddress').value,
            city: document.getElementById('city').value,
            state: document.getElementById('state').value,
            zipcode: document.getElementById('zipcode').value,
            membership_type: membershipType,
            auto_payment: true
        };

        console.log("Registering with membership type:", membershipType);

        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Registration failed');
        }

        console.log("Registration successful:", data);
        
        // Store the token using the same keys as in main.js
        localStorage.setItem('gym_token', data.access_token || data.token);
        if (data.refresh_token) {
            localStorage.setItem('gym_refresh_token', data.refresh_token);
        }
        localStorage.setItem('gym_user', JSON.stringify(data.user));

        // Use stored token for redirection
        const token = data.access_token || data.token;
        
        // Redirect based on role with token in URL
        if (data.user.role === 'admin') {
            window.location.href = `/admin/dashboard?token=${token}`;
        } else if (data.user.role === 'trainer') {
            window.location.href = `/trainer/dashboard?token=${token}`;
        } else {
            window.location.href = `/dashboard?token=${token}`;
        }
    } catch (error) {
        console.error('Registration error:', error);
        alert(error.message);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const nextBtns = document.querySelectorAll('.next');
    const prevBtns = document.querySelectorAll('.previous');
    const submitBtn = document.getElementById('submitBtn');
    const expirationInput = document.getElementById('expiration');

    nextBtns.forEach(btn => {
        btn.addEventListener('click', () => validateAndNext(currentPage + 1));
    });

    prevBtns.forEach(btn => {
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
