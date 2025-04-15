// Shared membership form handling
let currentPage = 0;
const totalPages = 4; // Including confirmation page

function validateAndNext(nextPageNum) {
    // Get the current page's inputs
    const currentInputs = document.querySelectorAll(`#page${currentPage + 1} input[required]`);
    let isValid = true;

    // Validate each required input
    currentInputs.forEach(input => {
        if (!input.checkValidity()) {
            isValid = false;
            input.reportValidity();
        }
    });

    // If all inputs are valid, move to next page
    if (isValid) {
        nextPage(nextPageNum);
    }
}

function nextPage(page) {
    // Hide current page
    document.querySelectorAll(".form-page").forEach(p => p.classList.remove("active"));
    
    // Show next page
    currentPage = page;
    document.querySelector(`#page${currentPage + 1}`).classList.add("active");

    // If we're on the confirmation page, update the confirmation details
    if (currentPage === 3) {
        updateConfirmation();
    }

    // Log for debugging
    console.log("Moving to page:", currentPage + 1);
}

function updateConfirmation() {
    // Helper function to safely get input value
    function getInputValue(id) {
        const element = document.getElementById(id);
        return element ? element.value : '';
    }

    // Helper function to safely update text content
    function updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    // Get all form values
    const fname = getInputValue("fname");
    const lname = getInputValue("lname");
    const email = getInputValue("email");
    const cardNumber = getInputValue("cardnumber");
    const expiration = getInputValue("expiration");
    const cardHolder = getInputValue("cardholdername");
    const address = getInputValue("streetaddress");
    const city = getInputValue("city");
    const state = getInputValue("state");
    const zipcode = getInputValue("zipcode");

    // Update confirmation fields
    updateElement("confirmName", `${fname} ${lname}`);
    updateElement("confirmEmail", email);
    updateElement("confirmCardnumber", cardNumber ? "*".repeat(12) + cardNumber.slice(-4) : '');
    updateElement("confirmExpiration", expiration);
    updateElement("confirmCardholder", cardHolder);
    updateElement("confirmStreetaddress", address);
    updateElement("confirmCity", city);
    updateElement("confirmState", state);
    updateElement("confirmZipcode", zipcode);

    console.log("Confirmation page updated");
}

async function submitForm(membershipType) {
    try {
        // Get form data
        const formData = {
            firstName: document.getElementById('fname').value,
            lastName: document.getElementById('lname').value,
            email: document.getElementById('email').value,
            password: document.getElementById('password').value,
            dob: document.getElementById('dob')?.value,
            cardNumber: document.getElementById('cardnumber').value,
            expiration: document.getElementById('expiration').value,
            securityCode: document.getElementById('securitycode').value,
            cardHolderName: document.getElementById('cardholdername').value,
            streetAddress: document.getElementById('streetaddress').value,
            city: document.getElementById('city').value,
            state: document.getElementById('state').value,
            zipCode: document.getElementById('zipcode').value
        };

        // Get CSRF token from meta tag
        const csrfMetaTag = document.querySelector('meta[name="csrf-token"]');
        if (!csrfMetaTag) {
            throw new Error("Security token not found. Please refresh the page and try again.");
        }
        const csrfToken = csrfMetaTag.content;
        if (!csrfToken) {
            throw new Error("Security token is invalid. Please refresh the page and try again.");
        }

        console.log("Membership type:", membershipType);

        // First register the user
        const registerResponse = await fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken
            },
            body: JSON.stringify({
                name: `${formData.firstName} ${formData.lastName}`,
                email: formData.email,
                password: formData.password,
                dob: formData.dob,
                address: formData.streetAddress,
                city: formData.city,
                state: formData.state,
                zipcode: formData.zipCode,
                auto_payment: true  // Set auto_payment to true by default
            })
        });

        if (!registerResponse.ok) {
            const errorData = await registerResponse.json();
            throw new Error(errorData.error || 'Registration failed');
        }

        // Parse the response only once and store the result
        const registerData = await registerResponse.json();
        const token = registerData.token;
        
        // Store token in localStorage
        localStorage.setItem('token', token);
        console.log("User registered successfully, token stored in localStorage");
        
        // Then add payment method
        const [month, year] = formData.expiration.split('/');
        const formattedExp = `20${year}-${month.padStart(2, '0')}-01`;

        const paymentData = {
            card_number: formData.cardNumber,
            exp: formattedExp,
            cvv: formData.securityCode,
            card_holder_name: formData.cardHolderName
        };

        console.log("Adding payment method");

        const paymentResponse = await fetch('/api/payment-methods', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
                'X-CSRF-Token': csrfToken
            },
            body: JSON.stringify(paymentData)
        });

        if (!paymentResponse.ok) {
            const errorData = await paymentResponse.json();
            throw new Error(errorData.error || 'Failed to add payment method');
        }

        const paymentMethod = await paymentResponse.json();
        console.log("Payment method added successfully:", paymentMethod);

        // Finally purchase membership
        const membershipData = {
            membership_type: membershipType,
            payment_method_id: paymentMethod.id
        };

        console.log("Purchasing membership:", membershipData);

        const membershipResponse = await fetch('/api/memberships/purchase', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
                'X-CSRF-Token': csrfToken
            },
            body: JSON.stringify(membershipData)
        });

        if (!membershipResponse.ok) {
            const errorData = await membershipResponse.json();
            throw new Error(errorData.error || 'Failed to purchase membership');
        }

        const membershipResult = await membershipResponse.json();
        console.log("Membership purchased successfully:", membershipResult);

        
        const msg = document.createElement('div');
        msg.textContent = 'Registration successful! Redirecting to dashboard...';
        msg.style.position = 'fixed';
        msg.style.top = '20px';
        msg.style.left = '50%';
        msg.style.transform = 'translateX(-50%)';
        msg.style.backgroundColor = '#ADD8E6';
        msg.style.color = 'white';
        msg.style.padding = '10px 20px';
        msg.style.borderRadius = '5px';
        msg.style.zIndex = 1000;
        document.body.appendChild(msg);

        setTimeout(() => {
            window.location.href = `/redirect-dashboard?token=${token}`;
        }, 1000);
        

    } catch (error) {
        console.error('Error:', error);
        alert(error.message || 'An error occurred during registration');
    }
}

// Add event listeners when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log("Setting up event listeners");
    
    // Get all buttons
    const nextButtons = [
        document.querySelector('#page1 button'),
        document.querySelector('#page2 button:last-child'),
        document.querySelector('#page3 button:last-child')
    ];

    const prevButtons = [
        document.querySelector('#page2 button:first-child'),
        document.querySelector('#page3 button:first-child'),
        document.querySelector('#page4 button:first-child')
    ];

    const submitButton = document.querySelector('#page4 button:last-child');

    // Add next button listeners
    nextButtons.forEach((button, index) => {
        if (button) {
            button.addEventListener('click', () => validateAndNext(index + 1));
            console.log(`Next button ${index + 1} listener added`);
        }
    });

    // Add previous button listeners
    prevButtons.forEach((button, index) => {
        if (button) {
            button.addEventListener('click', () => nextPage(index));
            console.log(`Previous button ${index + 1} listener added`);
        }
    });

    // Add submit button listener
    if (submitButton) {
        submitButton.addEventListener('click', () => {
            console.log("Submit button clicked");
            
            // First try to get membership type from window object
            let membership = undefined;
            
            try {
                // Check if the membershipType variable exists
                if (typeof membershipType !== 'undefined') {
                    console.log("Found membershipType as global variable:", membershipType);
                    membership = membershipType;
                }
                // If not, check if it's on the window object
                else if (typeof window.membershipType !== 'undefined') {
                    console.log("Found membershipType on window object:", window.membershipType);
                    membership = window.membershipType;
                }
                // If not found anywhere, try to determine from URL
                else {
                    console.log("Membership type not found in variables, checking URL");
                    const path = window.location.pathname;
                    if (path.includes('monthly')) {
                        console.log("Detected monthly membership from URL");
                        membership = 'monthly';
                    } else if (path.includes('annual')) {
                        console.log("Detected annual membership from URL");
                        membership = 'annual';
                    } else if (path.includes('student')) {
                        console.log("Detected student membership from URL");
                        membership = 'student';
                    }
                }
            } catch (e) {
                console.error("Error while determining membership type:", e);
            }
            
            if (!membership) {
                console.error("Membership type could not be determined");
                alert("Error: Membership type could not be determined. Please try again.");
                return;
            }
            
            console.log("Using membership type:", membership);
            submitForm(membership);
        });
        console.log("Submit button listener added");
    }

    // Form submission prevention
    const form = document.getElementById('registration');
    if (form) {
        form.addEventListener('submit', (e) => e.preventDefault());
        console.log("Form submit prevention added");
    }
    
    // Add expiration date formatting
    const expirationInput = document.getElementById('expiration');
    if (expirationInput) {
        expirationInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 2) {
                value = value.slice(0, 2) + '/' + value.slice(2, 4);
            }
            e.target.value = value;
        });
    }
}); 