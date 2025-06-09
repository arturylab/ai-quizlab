/**
 * AI QuizLab - Main JavaScript Module
 * Handles all frontend interactions for teachers and students
 */

document.addEventListener('DOMContentLoaded', function() {
    // ============================================================================
    // STUDENT UPLOAD FUNCTIONALITY (Section 1 in teacher.html)
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
    // STUDENT TABLE MANAGEMENT (Section 2 in teacher.html)
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
    // QUIZ CREATION FUNCTIONALITY (Section 3 in teacher.html)
    // ============================================================================
    
    /**
     * Handle checkbox changes to update AI status indicators
     */
    function initializeAiStatusIndicators() {
        const categories = ['math', 'physics', 'chemistry', 'biology', 'cs'];
        
        categories.forEach(category => {
            const checkbox = document.getElementById(`use_ai_${category}`);
            const statusSpan = document.querySelector(`.ai-status-${category}`);
            
            if (checkbox && statusSpan) {
                // Set initial status
                updateAiStatus(checkbox, statusSpan);
                
                // Add change listener
                checkbox.addEventListener('change', function() {
                    updateAiStatus(this, statusSpan);
                });
            }
        });
    }

    /**
     * Update AI status indicator based on checkbox state
     */
    function updateAiStatus(checkbox, statusSpan) {
        if (checkbox.checked) {
            statusSpan.style.color = '#ff6b35';
            statusSpan.style.fontWeight = 'bold';
        } else {
            statusSpan.style.color = '#1976d2';
            statusSpan.style.fontWeight = 'normal';
        }
    }

    /**
     * Handle unified quiz creation
     */
    const createQuizBtn = document.getElementById('createQuizBtn');
    if (createQuizBtn) {
        createQuizBtn.addEventListener('click', function() {
            handleUnifiedQuizCreation();
        });
    }

    /**
     * Simplified quiz creation handler - processes both AI and bank questions
     */
    function handleUnifiedQuizCreation() {
        const form = document.getElementById('quizCreationForm');
        const formData = new FormData(form);
        const messageDiv = document.getElementById('quizMessage');
        const createBtn = document.getElementById('createQuizBtn');

        // Analyze what categories are selected and how
        const analysis = analyzeQuizSelection(formData);
        
        if (analysis.totalQuestions === 0) {
            messageDiv.innerHTML = '<div style="color:red;">Please select at least one category with questions > 0.</div>';
            return;
        }

        // Disable button and show loading message
        createBtn.disabled = true;
        createBtn.textContent = '⏳ Creating Quiz...';
        
        const initialMessage = getInitialMessage(analysis);
        messageDiv.innerHTML = `<div style="color:blue;">${initialMessage}</div>`;

        // Send request to unified endpoint
        fetch('/create_unified_quiz', {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => response.json())
        .then(data => {
            // Re-enable button
            createBtn.disabled = false;
            createBtn.textContent = 'Create Quiz';

            if (data.success) {
                messageDiv.innerHTML = `<div style="color:green; font-weight:bold;">${data.message}</div>`;
            } else {
                messageDiv.innerHTML = `<div style="color:red;">${data.message}</div>`;
            }
        })
        .catch(error => {
            // Re-enable button
            createBtn.disabled = false;
            createBtn.textContent = 'Create Quiz';
            
            console.error('Quiz creation error:', error);
            messageDiv.innerHTML = '<div style="color:red;">Error creating quiz. Please try again.</div>';
        });
    }

    /**
     * Analyze quiz selection to determine what needs to be done
     */
    function analyzeQuizSelection(formData) {
        const categories = ['math', 'physics', 'chemistry', 'biology', 'cs'];
        const analysis = {
            totalQuestions: 0,
            hasAI: false,
            hasBank: false
        };

        categories.forEach(category => {
            const numQuestions = parseInt(formData.get(`num_questions_${category}`)) || 0;
            const useAI = formData.get(`use_ai_${category}`) === 'on';

            if (numQuestions > 0) {
                analysis.totalQuestions += numQuestions;
                
                if (useAI) {
                    analysis.hasAI = true;
                } else {
                    analysis.hasBank = true;
                }
            }
        });

        return analysis;
    }

    /**
     * Get initial message based on what's being processed
     */
    function getInitialMessage(analysis) {
        if (analysis.hasAI && analysis.hasBank) {
            return '🔄 Creating quiz with AI generation and question bank...';
        } else if (analysis.hasAI) {
            return '🤖 Generating quiz with AI...';
        } else {
            return '📚 Creating quiz from question bank...';
        }
    }

    // Initialize AI status indicators when page loads
    initializeAiStatusIndicators();

    // ============================================================================
    // QUIZ RESULT MANAGEMENT (Section 4 - Statistics in teacher.html)
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
    // TEACHER PROFILE EDITING (Section 5 - Menu/Profile in teacher.html)
    // ============================================================================
    const profileForm = document.getElementById('profileForm'); // Assuming the form has this ID
    
    const editNameBtn = document.getElementById('editNameBtn');
    const nameCell = document.getElementById('nameCell');
    const nameInput = document.getElementById('nameInput');

    const editSchoolBtn = document.getElementById('editSchoolBtn');
    const schoolCell = document.getElementById('schoolCell');
    const schoolInput = document.getElementById('schoolInput');

    const editPasswordBtn = document.getElementById('editPasswordBtn');
    const passwordDisplayRow = document.getElementById('passwordDisplayRow'); // CORRECTED ID
    const passwordEditRow = document.getElementById('passwordEditRow');
    const passwordInputField = document.getElementById('passwordInput'); // Renamed to avoid conflict
    const confirmPasswordInputField = document.getElementById('confirmPasswordInput'); // Renamed

    const updateProfileBtn = document.getElementById('updateProfileBtn');
    const cancelEditBtn = document.getElementById('cancelEditBtn');

    function setEditingState(isEditing) {
        if (cancelEditBtn) {
            cancelEditBtn.style.display = isEditing ? 'inline-block' : 'none';
        }
        // The UpdateProfile button generally remains visible.
        // If you wanted to hide/show it, you would do it here.
    }

    function enterFieldEditMode(pElement, inputElement) {
        if (pElement && inputElement) {
            pElement.style.display = 'none';
            inputElement.style.display = 'block';
            // inputElement.value = pElement.getAttribute('data-original'); // Ensures the input has the current value from <p>
            inputElement.focus();
        }
        setEditingState(true);
    }

    function exitAllEditModes() {
        // Reset Name field
        if (nameCell && nameInput) {
            nameCell.style.display = 'block'; // Or the original display of <p>
            nameInput.style.display = 'none';
            nameInput.value = nameCell.getAttribute('data-original'); // Restore input value
            nameCell.textContent = nameCell.getAttribute('data-original'); // Restore <p> text
        }
        // Reset School field
        if (schoolCell && schoolInput) {
            schoolCell.style.display = 'block'; // Or the original display of <p>
            schoolInput.style.display = 'none';
            schoolInput.value = schoolCell.getAttribute('data-original'); // Restore input value
            schoolCell.textContent = schoolCell.getAttribute('data-original'); // Restore <p> text
        }
        // Reset Password section
        if (passwordDisplayRow && passwordEditRow) {
            passwordDisplayRow.style.display = 'flex'; // .row in Bootstrap is flex
            passwordEditRow.style.display = 'none';
        }
        if (passwordInputField) passwordInputField.value = '';
        if (confirmPasswordInputField) confirmPasswordInputField.value = '';

        setEditingState(false);
    }

    if (editNameBtn) {
        editNameBtn.addEventListener('click', function() {
            enterFieldEditMode(nameCell, nameInput);
        });
    }

    if (editSchoolBtn) {
        editSchoolBtn.addEventListener('click', function() {
            enterFieldEditMode(schoolCell, schoolInput);
        });
    }

    if (editPasswordBtn) {
        editPasswordBtn.addEventListener('click', function() {
            if (passwordDisplayRow && passwordEditRow) {
                passwordDisplayRow.style.display = 'none';
                passwordEditRow.style.display = 'block';
                if(passwordInputField) passwordInputField.focus();
            }
            setEditingState(true);
        });
    }

    if (cancelEditBtn) {
        cancelEditBtn.addEventListener('click', function() {
            exitAllEditModes();
        });
    }

    // If the form is submitted (and not AJAX), the page will reload,
    // resetting the visual state. If it were AJAX, you would call exitAllEditModes()
    // in the successful response of the fetch.

    // Remove the previous toggleFieldEdit and resetFieldEdit functions if they are no longer used
    // or adapt them to the new logic if necessary.
    // The previous logic of toggleFieldEdit and resetFieldEdit has been integrated/replaced
    // by enterFieldEditMode and exitAllEditModes for more centralized management.

    // ============================================================================
    // QUIZ DELETION FUNCTIONALITY (Used in exam_teacher.html)
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

    // ============================================================================
    // STUDENT QUIZ FUNCTIONALITY (Used in quiz.html)
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
    
    const logoutButton = document.getElementById('logout'); // Make sure the ID matches your HTML
    if (logoutButton) {
        logoutButton.addEventListener('click', function(event) {
            event.preventDefault(); // Prevents the default action of the link (navigate to #)
            const logoutForm = document.getElementById('logoutForm');
            if (logoutForm) {
                logoutForm.submit(); // Submit the hidden form
            } else {
                console.error('Logout form not found!');
            }
        });
    }

    // ============================================================================
    // TOGGLE UPLOAD SECTION FUNCTIONALITY
    // ============================================================================
    const toggleUploadBtn = document.getElementById('toggleUploadSectionBtn');
    const uploadSectionContainer = document.getElementById('uploadSectionContainer');

    if (toggleUploadBtn && uploadSectionContainer) {
        toggleUploadBtn.addEventListener('click', function() {
            if (uploadSectionContainer.style.display === 'none') {
                uploadSectionContainer.style.display = 'block';
                this.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-dash-circle" viewBox="0 0 16 16">
                        <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                        <path d="M4 8a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7A.5.5 0 0 1 4 8z"/>
                    </svg>
                    Hide Uploader`;
            } else {
                uploadSectionContainer.style.display = 'none';
                this.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-plus-circle" viewBox="0 0 16 16">
                        <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                        <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/>
                    </svg>
                    Add Student List`;
            }
        });
    }

    // Script to update the custom file input label with the file name
    const studentCsvFileInput = document.getElementById('studentCsvFile');
    if (studentCsvFileInput) {
        studentCsvFileInput.addEventListener('change', function(e) {
            let fileName = "";
            if (this.files && this.files.length > 0) {
                fileName = this.files[0].name;
            }
            const nextSibling = this.nextElementSibling; // the label
            if (nextSibling) {
                nextSibling.innerText = fileName || "Choose CSV file...";
            }
        });
    }

    // ============================================================================
    // GENERIC TABLE SORTING FUNCTIONALITY
    // ============================================================================
    
    // Store sort state for each table separately
    const sortStates = {};

    function initializeTableSorting(tableId, columnMappings, defaultSortColumn = null) {
        const table = document.getElementById(tableId);
        if (!table) return;

        sortStates[tableId] = {
            currentSortColumn: defaultSortColumn,
            currentSortDirection: 'asc'
        };

        const headers = table.querySelectorAll('.sortable-header');
        headers.forEach(header => {
            header.addEventListener('click', function() {
                const column = this.dataset.column;
                const type = this.dataset.type;
                const currentTableState = sortStates[tableId];

                if (currentTableState.currentSortColumn === column) {
                    currentTableState.currentSortDirection = currentTableState.currentSortDirection === 'asc' ? 'desc' : 'asc';
                } else {
                    currentTableState.currentSortColumn = column;
                    currentTableState.currentSortDirection = 'asc';
                }

                updateSortIcons(headers, this, currentTableState.currentSortDirection);
                sortTable(table, column, type, currentTableState.currentSortDirection, columnMappings);
            });
        });

        // Initialize sort icons on page load for this table
        if (headers.length > 0) {
            updateSortIcons(headers, defaultSortColumn ? table.querySelector(`.sortable-header[data-column="${defaultSortColumn}"]`) : null, sortStates[tableId].currentSortDirection);
        }
    }

    // updateSortIcons function remains the same as you provided
    function updateSortIcons(headers, activeHeader, direction) {
        headers.forEach(header => {
            const icon = header.querySelector('.sort-icon');
            if (icon) {
                if (header === activeHeader) {
                    icon.textContent = direction === 'asc' ? ' ▲' : ' ▼';
                } else {
                    icon.textContent = ' ▲'; // Default icon for non-active sortable columns
                }
            }
        });
    }

    function sortTable(table, column, type, direction, columnMappings) {
        const tbody = table.querySelector('tbody');
        if (!tbody) return;
        const rows = Array.from(tbody.querySelectorAll('tr'));

        const colSpanForEmpty = table.id === 'studentsTable' ? 6 : 10; // Adjust based on table
        if (rows.length === 1 && rows[0].querySelectorAll('td').length === 1 && rows[0].querySelector('td').colSpan === colSpanForEmpty) {
            return; 
        }

        const dataRows = rows.map(row => {
            const cells = row.querySelectorAll('td');
            const rowData = { originalRow: row };
            for (const key in columnMappings) {
                const cellIndex = columnMappings[key];
                rowData[key] = cells[cellIndex] ? cells[cellIndex].textContent.trim() : '';
            }
            return rowData;
        });

        dataRows.sort((a, b) => {
            let valA = a[column];
            let valB = b[column];

            if (type === 'number') {
                valA = parseFloat(valA) || 0;
                valB = parseFloat(valB) || 0;
            } else if (type === 'string') {
                valA = (valA || "").toLowerCase();
                valB = (valB || "").toLowerCase();
            }

            if (valA < valB) {
                return direction === 'asc' ? -1 : 1;
            }
            if (valA > valB) {
                return direction === 'asc' ? 1 : -1;
            }
            return 0;
        });

        tbody.innerHTML = '';
        dataRows.forEach(dataRow => {
            tbody.appendChild(dataRow.originalRow);
        });
        
        // Re-attach specific event listeners if necessary (e.g., for studentsTable)
        if (table.id === 'studentsTable') {
            attachStudentEventListeners(); 
        } else if (table.id === 'statisticsTable') {
            attachStatisticsEventListeners(); // You'll need to create this if retry buttons need re-attaching
        }
    }

    // ============================================================================
    // INITIALIZE SORTING FOR SPECIFIC TABLES
    // ============================================================================
    
    // For Students Table
    const studentColumnMappings = {
        id: 0,
        name: 1,
        group: 2,
        username: 3
        // Add other columns if they become sortable
    };
    initializeTableSorting('studentsTable', studentColumnMappings, 'id'); // Default sort by ID

    // For Statistics Table
    const statisticsColumnMappings = {
        id: 0,       // Corresponds to student_id
        name: 1,
        group: 2,
        // mathematics: 3, // Not sortable by default in this request
        // physics: 4,
        // chemistry: 5,
        // biology: 6,
        // computer_science: 7,
        total: 8    // Corresponds to total score
    };
    initializeTableSorting('statisticsTable', statisticsColumnMappings, 'id'); // Default sort by ID

    // ============================================================================
    // EVENT LISTENERS FOR STATISTICS TABLE (Example, if needed)
    // ============================================================================
    function attachStatisticsEventListeners() {
        document.querySelectorAll('#statisticsTable .retry-quiz').forEach(function(btn) {
            // Check if listener already attached to prevent duplicates if not careful with re-attaching
            if (btn.dataset.listenerAttached === 'true') return;

            btn.onclick = function() {
                const studentId = this.dataset.studentId; // Using data-attribute
                const row = this.closest('tr');
                
                if (confirm(`Are you sure you want to allow student ID ${studentId} to retake the quiz? This will delete their previous results.`)) {
                    fetch('/reset_student_result', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ id: studentId })
                    }).then(res => res.json())
                    .then(data => {
                        if (data.success) {
                            row.remove(); // Or update UI as needed
                            // Potentially refresh or re-fetch statistics data
                        } else {
                            alert(data.message || 'Error resetting result');
                        }
                    });
                }
            };
            btn.dataset.listenerAttached = 'true'; // Mark as attached
        });
    }
    // Initial call for statistics table event listeners
    attachStatisticsEventListeners();


    // ============================================================================
    // STUDENT TABLE SORTING FUNCTIONALITY
    // ============================================================================
    let currentSortColumn = null;
    let currentSortDirection = 'asc'; // 'asc' or 'desc'

    const studentsTable = document.getElementById('studentsTable');
    if (studentsTable) {
        const headers = studentsTable.querySelectorAll('.sortable-header');
        headers.forEach(header => {
            header.addEventListener('click', function() {
                const column = this.dataset.column;
                const type = this.dataset.type;

                if (currentSortColumn === column) {
                    currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
                } else {
                    currentSortColumn = column;
                    currentSortDirection = 'asc';
                }

                updateSortIcons(headers, this, currentSortDirection);
                sortTable(studentsTable, column, type, currentSortDirection);
            });
        });

        // Initialize sort icons on page load
        const initialHeaders = studentsTable.querySelectorAll('.sortable-header');
        if (initialHeaders.length > 0) {
            // Set a default active column for initial icon display or show all as default
            // For simplicity, we'll make all non-active initially show ' ▲'
            updateSortIcons(initialHeaders, null, 'asc'); 
        }
    }

    function updateSortIcons(headers, activeHeader, direction) {
        headers.forEach(header => {
            const icon = header.querySelector('.sort-icon');
            if (icon) {
                if (header === activeHeader) {
                    icon.textContent = direction === 'asc' ? ' ▲' : ' ▼';
                } else {
                    icon.textContent = ' ▲'; // Default icon for non-active sortable columns
                }
            }
        });
    }

    function sortTable(table, column, type, direction) {
        const tbody = table.querySelector('tbody');
        if (!tbody) return; // Ensure tbody exists
        const rows = Array.from(tbody.querySelectorAll('tr'));

        // Handle case where there's only a "No students yet." row
        if (rows.length === 1 && rows[0].querySelectorAll('td').length === 1 && rows[0].querySelector('td').colSpan === 6) {
            return; // Do not sort if only the "No students" message is present
        }

        // Extract data from rows for sorting
        const dataRows = rows.map(row => {
            const cells = row.querySelectorAll('td');
            // Ensure cells exist for the required columns before accessing textContent
            return {
                id: cells[0] ? cells[0].textContent.trim() : '',
                name: cells[1] ? cells[1].textContent.trim() : '',
                group: cells[2] ? cells[2].textContent.trim() : '',
                username: cells[3] ? cells[3].textContent.trim() : '',
                originalRow: row // Store the original row to reconstruct it
            };
        });

        dataRows.sort((a, b) => {
            let valA = a[column];
            let valB = b[column];

            if (type === 'number') {
                valA = parseFloat(valA) || 0; // Fallback to 0 if parsing fails
                valB = parseFloat(valB) || 0;
            } else if (type === 'string') {
                valA = (valA || "").toLowerCase(); // Fallback to empty string if undefined
                valB = (valB || "").toLowerCase();
            }

            if (valA < valB) {
                return direction === 'asc' ? -1 : 1;
            }
            if (valA > valB) {
                return direction === 'asc' ? 1 : -1;
            }
            return 0;
        });

        // Clear tbody and re-add sorted rows
        tbody.innerHTML = '';
        dataRows.forEach(dataRow => {
            tbody.appendChild(dataRow.originalRow);
        });
        
        // Re-attach event listeners for edit/delete/reset as rows are re-ordered
        attachStudentEventListeners(); 
    }
});
