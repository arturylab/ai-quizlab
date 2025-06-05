/**
 * AI QuizLab - Main JavaScript Module
 * Handles all frontend interactions for teachers and students
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // ============================================================================
    // STUDENT QUIZ FUNCTIONALITY
    // ============================================================================
    
    /**
     * Handle student quiz submission via AJAX
     */
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
                    // Show success message and results summary
                    resultDiv.innerHTML = `<div style="color:green;font-weight:bold;">${data.message}</div><br>${data.summary}`;
                    form.style.display = 'none';
                    
                    // Show logout option after quiz completion
                    const logoutDiv = document.getElementById('logoutAfterQuiz');
                    if (logoutDiv) logoutDiv.style.display = 'block';
                } else {
                    resultDiv.innerHTML = `<div style="color:red;">${data.message}</div>`;
                }
            });
        });
    }

    // ============================================================================
    // STUDENT UPLOAD FUNCTIONALITY
    // ============================================================================
    
    /**
     * Handle CSV student upload with automatic password download
     */
    const uploadForm = document.getElementById('uploadStudentsForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const formData = new FormData(this);
            const messageDiv = document.getElementById('uploadMessage');
            
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
                    
                    // Display any upload errors
                    if (data.errors && data.errors.length > 0) {
                        message += '<div style="color:orange; font-size:14px; margin-top:10px;"><strong>Errors:</strong><br>';
                        data.errors.forEach(error => {
                            message += `• ${error}<br>`;
                        });
                        message += '</div>';
                    }
                    
                    messageDiv.innerHTML = message;
                    
                    // Auto-download passwords CSV if students were successfully added
                    if (data.students && data.students.length > 0) {
                        setTimeout(() => {
                            window.open('/download_passwords_csv', '_blank');
                        }, 1000);
                        
                        // Update the students table with new data
                        updateStudentsTable(data.students);
                    }
                    
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

    // ============================================================================
    // QUIZ CREATION FUNCTIONALITY
    // ============================================================================
    
    /**
     * Handle quiz creation with real-time progress tracking
     */
    const createQuizForm = document.getElementById('createQuizForm');
    if (createQuizForm) {
        createQuizForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const formData = new FormData(this);
            const messageDiv = document.getElementById('quizMessage');
            const progressContainer = document.getElementById('progressContainer');
            const progressBar = document.getElementById('progressBar');
            const progressText = document.getElementById('progressText');
            
            // Validate that at least one category is selected
            const totalCategories = getTotalCategories(formData);
            if (totalCategories === 0) {
                messageDiv.innerHTML = '<div style="color:red;">Please select at least one category with questions > 0.</div>';
                return;
            }
            
            // Initialize progress tracking UI
            messageDiv.innerHTML = '<div style="color:blue;">📚 Generating quiz from question bank...</div>';
            progressContainer.style.display = 'block';
            progressBar.style.width = '0%';
            progressText.textContent = 'Starting generation...';
            
            // Start real-time progress monitoring
            const progressInterval = startProgressTracking(progressBar, progressText);
            
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(response => response.json())
            .then(data => {
                // Clean up progress tracking
                clearInterval(progressInterval);
                progressBar.style.width = '100%';
                progressText.textContent = 'Completed!';
                
                // Show final result after brief delay
                setTimeout(() => {
                    progressContainer.style.display = 'none';
                    
                    if (data.success) {
                        messageDiv.innerHTML = `<div style="color:green; font-weight:bold;">${data.message}</div>`;
                    } else {
                        messageDiv.innerHTML = `<div style="color:red;">${data.message}</div>`;
                    }
                }, 1000);
            })
            .catch(error => {
                clearInterval(progressInterval);
                progressContainer.style.display = 'none';
                console.error('Create quiz error:', error);
                messageDiv.innerHTML = '<div style="color:red;">Error creating quiz. Please try again.</div>';
            });
        });
    }

    /**
     * Real-time progress tracking for quiz generation
     * Polls the server every 500ms for progress updates
     */
    function startProgressTracking(progressBar, progressText) {
        return setInterval(() => {
            fetch('/quiz_progress', {
                method: 'GET',
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'processing') {
                    // Update progress bar (cap at 95% until completion)
                    const percentage = Math.min(data.percentage, 95);
                    progressBar.style.width = percentage + '%';
                    progressText.textContent = data.message || 'Processing...';
                } else if (data.status === 'completed') {
                    progressBar.style.width = '100%';
                    progressText.textContent = 'Finalizing...';
                } else if (data.status === 'error') {
                    progressBar.style.width = '100%';
                    progressText.textContent = 'Error occurred';
                }
            })
            .catch(error => {
                console.log('Progress tracking error:', error);
            });
        }, 500);
    }

    /**
     * Count how many quiz categories have questions > 0
     */
    function getTotalCategories(formData) {
        let count = 0;
        const categories = ['math', 'physics', 'chemistry', 'biology', 'cs'];
        
        categories.forEach(category => {
            const numQuestions = formData.get(`num_questions_${category}`);
            if (numQuestions && parseInt(numQuestions) > 0) {
                count++;
            }
        });
        
        return count;
    }

    // ============================================================================
    // TEACHER PROFILE EDITING
    // ============================================================================
    
    /**
     * Handle profile field editing functionality
     */
    const editNameBtn = document.getElementById('editNameBtn');
    const editSchoolBtn = document.getElementById('editSchoolBtn');
    const editPasswordBtn = document.getElementById('editPasswordBtn');
    const cancelEditBtn = document.getElementById('cancelEditBtn');

    if (editNameBtn) {
        editNameBtn.addEventListener('click', function() {
            toggleFieldEdit('nameCell', 'name', 'Name');
        });
    }

    if (editSchoolBtn) {
        editSchoolBtn.addEventListener('click', function() {
            toggleFieldEdit('schoolCell', 'school', 'School');
        });
    }

    if (editPasswordBtn) {
        editPasswordBtn.addEventListener('click', function() {
            const passwordRow = document.getElementById('passwordRow');
            const passwordEditRow = document.getElementById('passwordEditRow');
            
            if (passwordRow && passwordEditRow) {
                passwordRow.style.display = 'none';
                passwordEditRow.style.display = 'table-row';
            }
        });
    }

    if (cancelEditBtn) {
        cancelEditBtn.addEventListener('click', function() {
            // Reset all editing states
            resetFieldEdit('nameCell');
            resetFieldEdit('schoolCell');
            
            // Hide password edit interface
            const passwordRow = document.getElementById('passwordRow');
            const passwordEditRow = document.getElementById('passwordEditRow');
            const passwordInput = document.getElementById('passwordInput');
            const confirmPasswordInput = document.getElementById('confirmPasswordInput');
            
            if (passwordRow && passwordEditRow) {
                passwordRow.style.display = 'table-row';
                passwordEditRow.style.display = 'none';
            }
            
            if (passwordInput) passwordInput.value = '';
            if (confirmPasswordInput) confirmPasswordInput.value = '';
        });
    }

    /**
     * Toggle a field between display and edit mode
     */
    function toggleFieldEdit(cellId, fieldName, placeholder) {
        const cell = document.getElementById(cellId);
        if (!cell || cell.querySelector('input')) return;

        const currentValue = cell.textContent;
        cell.innerHTML = `<input type="text" name="${fieldName}" value="${currentValue}" placeholder="${placeholder}" style="width:100%; padding:4px;">`;
        
        const input = cell.querySelector('input');
        if (input) {
            input.focus();
            input.select();
        }
    }

    /**
     * Reset a field from edit mode to display mode
     */
    function resetFieldEdit(cellId) {
        const cell = document.getElementById(cellId);
        if (!cell) return;

        const originalValue = cell.getAttribute('data-original');
        cell.textContent = originalValue;
    }

    // ============================================================================
    // STUDENT TABLE MANAGEMENT
    // ============================================================================
    
    /**
     * Update the students table with new data
     */
    function updateStudentsTable(students) {
        const tbody = document.querySelector('#studentsTable tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (students.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">No students yet.</td></tr>';
            return;
        }
        
        // Build table rows for each student
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

    /**
     * Attach event listeners to student management buttons
     * Handles edit, delete, and password reset functionality
     */
    function attachStudentEventListeners() {
        // Edit student functionality
        document.querySelectorAll('.edit-student').forEach(function(btn) {
            btn.onclick = function() {
                const row = btn.closest('tr');
                const nameCell = row.querySelector('.editable-name');
                const groupCell = row.querySelector('.editable-group');
                
                if (!nameCell.querySelector('input')) {
                    // Switch to edit mode
                    const name = nameCell.textContent;
                    const group = groupCell.textContent;
                    nameCell.innerHTML = `<input type="text" value="${name}" style="width:90%;">`;
                    groupCell.innerHTML = `<input type="text" value="${group}" style="width:90%;">`;
                    btn.innerHTML = '💾';
                    btn.title = 'Save';
                    
                    // Create save function for this specific button
                    const saveFunction = function() {
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
                                // Switch back to display mode
                                nameCell.textContent = data.name;
                                groupCell.textContent = data.group;
                                btn.innerHTML = '✏️';
                                btn.title = 'Edit';
                                attachStudentEventListeners();
                            } else {
                                alert(data.message || 'Error updating student');
                            }
                        });
                    };
                    
                    btn.onclick = saveFunction;
                }
            };
        });

        // Delete student functionality
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

        // Reset student password functionality
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

    // Initialize student event listeners on page load
    attachStudentEventListeners();

    // ============================================================================
    // QUIZ RESULT MANAGEMENT
    // ============================================================================
    
    /**
     * Handle retry quiz functionality for students
     */
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

    // ============================================================================
    // QUIZ DELETION FUNCTIONALITY
    // ============================================================================
    
    /**
     * Handle quiz deletion with confirmation
     */
    const deleteQuizBtn = document.getElementById('deleteQuizBtn');
    if (deleteQuizBtn) {
        deleteQuizBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to delete this quiz? This action cannot be undone.')) {
                const messageDiv = document.getElementById('deleteMessage');
                
                messageDiv.innerHTML = '<div style="color:blue;">Deleting quiz...</div>';
                
                fetch('/delete_quiz', {
                    method: 'POST',
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        messageDiv.innerHTML = `<div style="color:green; font-weight:bold;">${data.message}</div>`;
                        // Redirect to teacher dashboard after successful deletion
                        setTimeout(() => {
                            window.location.href = '/teacher';
                        }, 2000);
                    } else {
                        messageDiv.innerHTML = `<div style="color:red;">${data.message}</div>`;
                    }
                })
                .catch(error => {
                    console.error('Delete quiz error:', error);
                    messageDiv.innerHTML = '<div style="color:red;">Error deleting quiz. Please try again.</div>';
                });
            }
        });
    }
});