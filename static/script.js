document.addEventListener('DOMContentLoaded', function() {
    // Quiz form AJAX
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
                    const logoutDiv = document.getElementById('logoutAfterQuiz');
                    if (logoutDiv) logoutDiv.style.display = 'block';
                } else {
                    resultDiv.innerHTML = `<div style="color:red;">${data.message}</div>`;
                }
            });
        });
    }

    // Create quiz AJAX
    const createQuizForm = document.getElementById('createQuizForm');
    if (createQuizForm) {
        createQuizForm.addEventListener('submit', function(event) {
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
    }

    // Edit student
    document.querySelectorAll('.edit-student').forEach(function(btn) {
        btn.onclick = function() {
            const row = btn.closest('tr');
            const nameCell = row.querySelector('.editable-name');
            const groupCell = row.querySelector('.editable-group');
            if (!nameCell.querySelector('input')) {
                const name = nameCell.textContent;
                const group = groupCell.textContent;
                nameCell.innerHTML = `<input type="text" value="${name}" style="width:90%;">`;
                groupCell.innerHTML = `<input type="text" value="${group}" style="width:90%;">`;
                btn.innerHTML = '💾';
                btn.title = 'Save';
                btn.onclick = function() {
                    fetch('/edit_student', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            id: row.dataset.studentId,
                            name: nameCell.querySelector('input').value,
                            group: groupCell.querySelector('input').value
                        })
                    }).then(res => res.json())
                    .then(data => {
                        if (data.success) {
                            nameCell.textContent = data.name;
                            groupCell.textContent = data.group;
                            btn.innerHTML = '✏️';
                            btn.title = 'Edit';
                            btn.onclick = arguments.callee;
                        } else {
                            alert(data.message || 'Error updating student');
                        }
                    });
                };
            }
        };
    });

    // Delete student
    document.querySelectorAll('.delete-student').forEach(function(btn) {
        btn.onclick = function() {
            if (confirm('Are you sure you want to delete this student?')) {
                const row = btn.closest('tr');
                fetch('/delete_student', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ id: row.dataset.studentId })
                }).then(res => res.json())
                .then(data => {
                    if (data.success) {
                        row.remove();
                    } else {
                        alert(data.message || 'Error deleting student');
                    }
                });
            }
        };
    });

    // Reset student password
    document.querySelectorAll('.reset-password').forEach(function(btn) {
        btn.onclick = function() {
            const row = btn.closest('tr');
            fetch('/reset_student_password', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ id: row.dataset.studentId })
            }).then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert("New password for the student: " + data.password);
                } else {
                    alert(data.message || 'Error resetting password');
                }
            });
        };
    });

    // Retry quiz
    document.querySelectorAll('.retry-quiz').forEach(function(btn) {
        btn.onclick = function() {
            const row = btn.closest('tr');
            const studentId = row.querySelector('td').textContent;
            if (confirm('Are you sure you want to allow this student to retake the quiz? This will delete their previous results.')) {
                fetch('/reset_student_result', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ id: studentId })
                }).then(res => res.json())
                .then(data => {
                    if (data.success) {
                        row.remove();
                    } else {
                        alert(data.message || 'Error resetting result');
                    }
                });
            }
        };
    });
});