let currentPage = 0;

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

async function submitForm() {
    try {
        const formData = {
            name: `${document.getElementById("fname").value} ${document.getElementById("lname").value}`,
            email: document.getElementById("email").value,
            password: document.getElementById("password").value,
            dob: document.getElementById("dob").value,
            address: document.getElementById("streetaddress").value,
            city: document.getElementById("city").value,
            state: document.getElementById("state").value,
            zipcode: document.getElementById("zipcode").value,
            auto_payment: true
        };

        console.log("Sending registration data...");

        // Register user
        const response = await fetch("/api/register", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || "Registration failed");
        }

        const responseData = await response.json();
        const token = responseData.token;
        
        if (!token) {
            throw new Error("No authentication token received");
        }

        // Store token
        localStorage.setItem('token', token);
        console.log("Token stored successfully");

        // Format payment data
        const expDate = document.getElementById("expiration").value;
        const [month, year] = expDate.split("/");
        const formattedExp = `20${year}-${month.padStart(2, '0')}-01`;

        const paymentData = {
            card_number: document.getElementById("cardnumber").value,
            exp: formattedExp,
            cvv: document.getElementById("securitycode").value,
            card_holder_name: document.getElementById("cardholdername").value,
            saved: true
        };

        console.log("Sending payment method data...");
        
        // Create payment method
        const paymentMethodResponse = await fetch("/api/dashboard/payment-methods", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(paymentData)
        });

        if (!paymentMethodResponse.ok) {
            let errorMessage;
            try {
                const errorData = await paymentMethodResponse.json();
                errorMessage = errorData.error;
            } catch (e) {
                errorMessage = "Failed to save payment method";
            }
            throw new Error(errorMessage);
        }

        const paymentMethodData = await paymentMethodResponse.json();
        if (!paymentMethodData.id) {
            throw new Error("Payment method created but no ID returned");
        }

        console.log("Payment method created successfully");

        // Purchase membership
        console.log("Purchasing membership...");
        
        const membershipData = {
            membership_type: "monthly",
            payment_method_id: paymentMethodData.id
        };
        
        const membershipResponse = await fetch("/api/memberships/purchase", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(membershipData)
        });

        if (!membershipResponse.ok) {
            const errorData = await membershipResponse.json();
            throw new Error(errorData.error || "Failed to purchase membership");
        }

        alert("Registration successful! Redirecting to dashboard...");
        window.location.href = "/dashboard";

    } catch (error) {
        console.error("Error:", error);
        alert(error.message || "An error occurred during registration");
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
        submitButton.addEventListener('click', submitForm);
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
            if (value.length >= 2) {
                value = value.slice(0,2) + '/' + value.slice(2,4);
            }
            e.target.value = value;
            
            // Validate month is between 01-12
            if (value.length >= 2) {
                const month = parseInt(value.slice(0,2));
                if (month < 1 || month > 12) {
                    e.target.setCustomValidity('Month must be between 01 and 12');
                } else {
                    e.target.setCustomValidity('');
                }
            }
            
            // Validate year is not in the past
            if (value.length === 5) {
                const [month, year] = value.split('/');
                const currentYear = new Date().getFullYear() % 100; // Get last 2 digits
                const currentMonth = new Date().getMonth() + 1; // 1-12
                
                if (parseInt(year) < currentYear || 
                    (parseInt(year) === currentYear && parseInt(month) < currentMonth)) {
                    e.target.setCustomValidity('Expiration date cannot be in the past');
                } else {
                    e.target.setCustomValidity('');
                }
            }
        });
        
        // Add placeholder and pattern
        expirationInput.setAttribute('placeholder', 'MM/YY');
        expirationInput.setAttribute('pattern', '^(0[1-9]|1[0-2])/([0-9]{2})$');
        expirationInput.setAttribute('maxlength', '5');
    }
    
    console.log("Form script loaded and initialized");
}); 