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

    // Upload students AJAX (with automatic download)
    const uploadForm = document.getElementById('uploadStudentsForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const formData = new FormData(this);
            const messageDiv = document.getElementById('uploadMessage');
            
            // Show loading message
            messageDiv.innerHTML = '<div style="color:blue;">Uploading students...</div>';
            
            fetch('/upload', {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    let message = `<div style="color:green;">${data.message}</div>`;
                    
                    // Show errors if any
                    if (data.errors && data.errors.length > 0) {
                        message += '<div style="color:orange; font-size:14px; margin-top:10px;"><strong>Errors:</strong><br>';
                        data.errors.forEach(error => {
                            message += `• ${error}<br>`;
                        });
                        message += '</div>';
                    }
                    
                    messageDiv.innerHTML = message;
                    
                    // Automatically trigger CSV download if students were added
                    if (data.students && data.students.length > 0) {
                        // Add a brief delay to show the success message
                        setTimeout(() => {
                            window.open('/download_passwords_csv', '_blank');
                        }, 1000);
                    }
                    
                    // Refresh the students table
                    if (data.students && data.students.length > 0) {
                        updateStudentsTable(data.students);
                    }
                    // Clear the file input
                    this.reset();
                } else {
                    messageDiv.innerHTML = `<div style="color:red;">${data.message}</div>`;
                }
            })
            .catch(error => {
                messageDiv.innerHTML = '<div style="color:red;">Error uploading file. Please try again.</div>';
                console.error('Upload error:', error);
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

    // Function to update students table
    function updateStudentsTable(students) {
        const tbody = document.querySelector('#studentsTable tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (students.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">No students yet.</td></tr>';
            return;
        }
        
        students.forEach(student => {
            const row = document.createElement('tr');
            row.setAttribute('data-student-id', student.id);
            row.innerHTML = `
                <td>${student.id}</td>
                <td class="editable-name">${student.name}</td>
                <td class="editable-group">${student.group}</td>
                <td>${student.username}</td>
                <td>
                    ********
                    <span class="reset-password" style="cursor:pointer; margin-left:8px;" title="Reset Password">🔄</span>
                </td>
                <td>
                    <span class="edit-student" style="cursor:pointer;" title="Edit">✏️</span>
                    <span class="delete-student" style="cursor:pointer; margin-left:8px;" title="Delete">❌</span>
                </td>
            `;
            tbody.appendChild(row);
        });
        
        // Re-attach event listeners for new elements
        attachStudentEventListeners();
    }

    // Function to attach event listeners to student management buttons
    function attachStudentEventListeners() {
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
    }

    // Initial attachment of event listeners
    attachStudentEventListeners();

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