document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('studentQuizForm');
    if (form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            const formData = new FormData(form);
            fetch("/submit_quiz", {
                method: "POST",
                body: formData,
                headers: {'X-Requested-With': 'XMLHttpRequest'}
            })
            .then(response => response.json())
            .then(data => {
                const resultDiv = document.getElementById('quizResult');
                if (data.success) {
                    resultDiv.innerHTML = `<div style="color:green;font-weight:bold;">${data.message}</div><br>${data.summary}`;
                    form.style.display = 'none';
                    // Mostrar el botón de logout
                    const logoutDiv = document.getElementById('logoutAfterQuiz');
                    if (logoutDiv) logoutDiv.style.display = 'block';
                } else {
                    resultDiv.innerHTML = `<div style="color:red;">${data.message}</div>`;
                }
            });
        });
    }

    document.getElementById('createQuizForm').addEventListener('submit', function(event) {
        event.preventDefault();
        const formData = new FormData(this);
        fetch(this.action, {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('quizMessage').textContent = data.message;
        });
    });
});