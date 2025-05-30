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
                    // Mostrar el botón de logout
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

    // Name edit toggle
    const editNameBtn = document.getElementById('editNameBtn');
    if (editNameBtn) {
        editNameBtn.onclick = function() {
            const nameCell = document.getElementById('nameCell');
            if (!document.getElementById('nameInput')) {
                const currentName = nameCell.textContent;
                nameCell.innerHTML = `<input type="text" id="nameInput" name="name" value="${currentName}" style="width:100%;">`;
                document.getElementById('nameInput').focus();
            }
            // Si ya existe el input, no hace nada
        };
    }

    // Email edit toggle
    const editEmailBtn = document.getElementById('editEmailBtn');
    if (editEmailBtn) {
        editEmailBtn.onclick = function() {
            const emailCell = document.getElementById('emailCell');
            if (!document.getElementById('emailInput')) {
                const currentEmail = emailCell.textContent;
                emailCell.innerHTML = `<input type="email" id="emailInput" name="email" value="${currentEmail}" style="width:100%;">`;
                document.getElementById('emailInput').focus();
            }
            // Si ya existe el input, no hace nada
        };
    }

    // Password edit toggle
    const editPasswordBtn = document.getElementById('editPasswordBtn');
    if (editPasswordBtn) {
        editPasswordBtn.onclick = function() {
            const passwordEditRow = document.getElementById('passwordEditRow');
            if (passwordEditRow.style.display === "none") {
                passwordEditRow.style.display = "";
                document.getElementById('passwordInput').focus();
            }
            // Si ya está visible, no hace nada
        };
    }

    // School edit toggle
    const editSchoolBtn = document.getElementById('editSchoolBtn');
    if (editSchoolBtn) {
        editSchoolBtn.onclick = function() {
            const schoolCell = document.getElementById('schoolCell');
            if (!document.getElementById('schoolInput')) {
                const currentSchool = schoolCell.textContent;
                schoolCell.innerHTML = `<input type="text" id="schoolInput" name="school" value="${currentSchool}" style="width:100%;">`;
                document.getElementById('schoolInput').focus();
            }
            // Si ya existe el input, no hace nada
        };
    }

    // Habilita los campos antes de enviar el formulario de perfil
    const profileForm = document.querySelector('form[action$="profile"]');
    if (profileForm) {
        profileForm.addEventListener('submit', function() {
            const nameInput = document.getElementById('nameInput');
            if (nameInput) nameInput.disabled = false;
            const emailInput = document.getElementById('emailInput');
            if (emailInput) emailInput.disabled = false;
            const schoolInput = document.getElementById('schoolInput');
            if (schoolInput) schoolInput.disabled = false;
        });
    }

    const cancelEditBtn = document.getElementById('cancelEditBtn');
    if (cancelEditBtn) {
        cancelEditBtn.onclick = function() {
            // Restaurar Name
            const nameCell = document.getElementById('nameCell');
            if (nameCell) {
                const originalName = nameCell.getAttribute('data-original');
                nameCell.innerHTML = originalName;
                nameCell.setAttribute('data-original', originalName);
            }
            // Restaurar Email
            const emailCell = document.getElementById('emailCell');
            if (emailCell) {
                const originalEmail = emailCell.getAttribute('data-original');
                emailCell.innerHTML = originalEmail;
                emailCell.setAttribute('data-original', originalEmail);
            }
            // Restaurar School
            const schoolCell = document.getElementById('schoolCell');
            if (schoolCell) {
                const originalSchool = schoolCell.getAttribute('data-original');
                schoolCell.innerHTML = originalSchool;
                schoolCell.setAttribute('data-original', originalSchool);
            }
            // Ocultar edición de password y limpiar campos
            const passwordEditRow = document.getElementById('passwordEditRow');
            if (passwordEditRow) {
                passwordEditRow.style.display = "none";
                const passwordInput = document.getElementById('passwordInput');
                const confirmPasswordInput = document.getElementById('confirmPasswordInput');
                if (passwordInput) passwordInput.value = "";
                if (confirmPasswordInput) confirmPasswordInput.value = "";
            }
        };
    }

    // Editar estudiante
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

    // Eliminar estudiante
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
                    // Actualiza el password en la celda
                    btn.parentElement.childNodes[0].textContent = data.password;
                } else {
                    alert(data.message || 'Error resetting password');
                }
            });
        };
    });

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