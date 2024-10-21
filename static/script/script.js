document.getElementById('loginForm').addEventListener('submit', function(event) {
    event.preventDefault();  // Prevent form from submitting immediately

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    if (username === '' || password === '') {
        document.getElementById('error-msg').textContent = 'Both fields are required!';
    } else {
        // Here, you can add more client-side validation if needed
        this.submit();  // Submit the form after validation
    }
});
