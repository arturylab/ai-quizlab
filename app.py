import csv
import time
from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify, flash
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash
from datetime import timedelta
from config import Config
from models import db, Teacher, Student, Result, Quiz, QuizQuestion
from functools import wraps

# Import utility functions
from utils import (
    get_json_path, read_json, write_json, generate_random_password,
    create_csv_response, validate_form_data
)
from quiz_utils import (
    load_questions_from_bank, create_generation_report, calculate_quiz_scores,
    create_result_data, format_result_summary, parse_ai_csv_to_quiz_questions
)
from ai_quiz import QuizGenerator

# ============================================================================
# APPLICATION INITIALIZATION
# ============================================================================

app = Flask(__name__)
app.config.from_object(Config)
app.permanent_session_lifetime = timedelta(minutes=30)

# Initialize database and migrations
db.init_app(app)
migrate = Migrate(app, db)

# ============================================================================
# AUTHENTICATION DECORATORS
# ============================================================================

def teacher_required(f):
    """
    Decorator to ensure user is logged in as a teacher.
    
    Returns JSON response for AJAX requests or redirects for normal requests.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'teacher_id' not in session:
            if request.is_json:
                return jsonify(success=False, message="Teacher authentication required")
            flash('Please log in as a teacher to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    """
    Decorator to ensure user is logged in as a student.
    
    Returns JSON response for AJAX requests or redirects for normal requests.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'student_id' not in session:
            if request.is_json:
                return jsonify(success=False, message="Student authentication required")
            flash('Please log in as a student to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_teacher():
    """
    Retrieve the current logged-in teacher from the database.
    
    Returns:
        Teacher: Teacher object if found, None otherwise
    """
    teacher_id = session.get('teacher_id')
    if teacher_id:
        return db.session.get(Teacher, teacher_id)
    return None

def get_student():
    """
    Retrieve the current logged-in student from the database.
    
    Returns:
        Student: Student object if found, None otherwise
    """
    student_id = session.get('student_id')
    if student_id:
        return db.session.get(Student, student_id)
    return None

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main entry point - redirects to login page."""
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user authentication for both teachers and students.
    
    Attempts teacher login first, then student login if teacher fails.
    Sets session data and redirects to appropriate dashboard.
    """
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Validate input
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('login.html')

        # Try teacher authentication first
        teacher = Teacher.query.filter_by(username=username).first()
        if teacher and teacher.check_password(password):
            session['teacher_id'] = teacher.id
            session.permanent = True
            flash('Login successful! Welcome, teacher.', 'success')
            return redirect(url_for('teacher'))

        # Try student authentication
        student = Student.query.filter_by(username=username).first()
        if student and student.check_password(password):
            session['student_id'] = student.id
            session.permanent = True
            flash('Login successful! Welcome, student.', 'success')
            return redirect(url_for('student'))

        # Authentication failed
        flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    """Clear user session and redirect to login page."""
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle teacher registration with validation.
    
    Validates form data, checks for existing usernames/emails,
    and creates new teacher account with hashed password.
    """
    if request.method == 'POST':
        # Extract and sanitize form data
        form_data = {
            'name': request.form.get('name', '').strip(),
            'email': request.form.get('email', '').strip(),
            'school': request.form.get('school', '').strip(),
            'username': request.form.get('username', '').strip(),
            'password': request.form.get('password', ''),
            'confirm_password': request.form.get('confirm_password', '')
        }

        # Validate required fields
        errors = validate_form_data(form_data, ['name', 'email', 'school', 'username', 'password'])
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html')

        # Check password confirmation
        if form_data['password'] != form_data['confirm_password']:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        # Check for existing username and email
        if Teacher.query.filter_by(username=form_data['username']).first():
            flash('Username already exists. Please choose another.', 'danger')
            return render_template('register.html')

        if Teacher.query.filter_by(email=form_data['email']).first():
            flash('Email already registered. Please use another.', 'danger')
            return render_template('register.html')

        # Create new teacher account
        try:
            new_teacher = Teacher(
                name=form_data['name'],
                email=form_data['email'],
                school=form_data['school'],
                username=form_data['username'],
                password=generate_password_hash(form_data['password'])
            )
            db.session.add(new_teacher)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'danger')
            print(f"Registration error: {e}")

    return render_template('register.html')

# ============================================================================
# TEACHER DASHBOARD ROUTES
# ============================================================================

@app.route('/teacher')
@teacher_required
def teacher():
    """
    Teacher dashboard displaying students and exam results.
    
    Shows list of registered students and their quiz results.
    """
    teacher = get_teacher()
    students_list = Student.query.filter_by(teacher_id=teacher.id).all()
    results_list = Result.query.join(Student, Result.student_id == Student.id)\
        .filter(Student.teacher_id == teacher.id).all()
    
    return render_template(
        'teacher.html',
        teacher_name=teacher.name,
        students_list=students_list,
        results_list=results_list
    )

@app.route('/profile', methods=['GET', 'POST'])
@teacher_required
def profile():
    """
    Handle teacher profile management and updates.
    
    Allows teachers to update name, school, and password.
    """
    teacher = get_teacher()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        school = request.form.get('school', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Update profile fields
        updated = False
        if name and name != teacher.name:
            teacher.name = name
            updated = True
        if school and school != teacher.school:
            teacher.school = school
            updated = True
        
        # Handle password update
        if password:
            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return render_template('profile.html', teacher=teacher)
            teacher.password = generate_password_hash(password)
            updated = True

        # Save changes to database
        if updated:
            try:
                db.session.commit()
                flash('Profile updated successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Update failed. Please try again.', 'danger')
                print(f"Profile update error: {e}")

        return redirect(url_for('profile'))

    return render_template('profile.html', teacher=teacher)

# ============================================================================
# STUDENT MANAGEMENT ROUTES
# ============================================================================

@app.route('/upload', methods=['POST'])
@teacher_required
def upload_students():
    """
    Handle CSV file upload for bulk student registration.
    
    Processes CSV file containing student data (exp, name, group),
    creates accounts with random passwords, and returns password list.
    """
    file = request.files.get('file')
    if not file or not file.filename.endswith('.csv'):
        error_msg = 'Invalid file. Please upload a CSV file.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message=error_msg)
        flash(error_msg, 'danger')
        return redirect(url_for('teacher'))

    try:
        # Process CSV file
        csvfile = file.stream.read().decode('utf-8').splitlines()
        reader = csv.DictReader(csvfile)
        passwords_to_deliver = []
        errors = []
        students_added = []

        for idx, row in enumerate(reader, start=2):
            # Extract and validate row data
            exp = str(row.get('exp', '')).strip()
            name = row.get('name', '').strip()
            group = row.get('group', '').strip()
            username = exp

            # Validation checks
            if not name:
                errors.append(f"Row {idx}: Name is required.")
                continue
            if not group:
                errors.append(f"Row {idx}: Group is required.")
                continue
            if not username:
                errors.append(f"Row {idx}: Username is required.")
                continue
            if Student.query.filter_by(username=username).first():
                errors.append(f"Row {idx}: Username '{username}' already exists. Skipped.")
                continue

            # Create student with random password
            password_plain = generate_random_password(6)
            password_hash = generate_password_hash(password_plain)

            student = Student(
                name=name,
                group=group,
                username=username,
                password=password_hash,
                teacher_id=session['teacher_id']
            )
            db.session.add(student)
            db.session.flush()  # Get the ID without committing

            # Store password for delivery
            passwords_to_deliver.append({
                "ID": student.id,
                "Name": name,
                "Group": group,
                "Username": username,
                "Password": password_plain
            })
            
            students_added.append({
                "id": student.id,
                "name": name,
                "group": group,
                "username": username
            })

        # Commit all changes
        db.session.commit()
        session['passwords_to_deliver'] = passwords_to_deliver

        # Return response based on request type
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            message = f"Successfully uploaded {len(students_added)} students!"
            if errors:
                message += f" {len(errors)} students were skipped due to errors."
            
            return jsonify(
                success=True, 
                message=message,
                students=students_added,
                errors=errors
            )

        # Handle regular form submission
        if errors:
            flash('Some students were not added:<br>' + '<br>'.join(errors), 'warning')

        return redirect(url_for('download_passwords_csv'))

    except Exception as e:
        db.session.rollback()
        error_msg = 'Error processing CSV file. Please check the format.'
        print(f"CSV upload error: {e}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message=error_msg)
        
        flash(error_msg, 'danger')
        return redirect(url_for('teacher'))

@app.route('/edit_student', methods=['POST'])
@teacher_required
def edit_student():
    """
    Handle student information editing via AJAX.
    
    Updates student name and group after validation.
    """
    data = request.get_json()
    student_id = data.get('id')
    new_name = data.get('name', '').strip()
    new_group = data.get('group', '').strip()

    # Validate input data
    if not student_id or not new_name or not new_group:
        return jsonify(success=False, message="All fields are required.")

    try:
        # Find and authorize student
        student_db = db.session.get(Student, int(student_id))
        if not student_db:
            return jsonify(success=False, message="Student not found.")
        
        if student_db.teacher_id != session['teacher_id']:
            return jsonify(success=False, message="Not authorized to edit this student.")

        # Update student information
        student_db.name = new_name
        student_db.group = new_group
        db.session.commit()
        
        return jsonify(success=True, name=new_name, group=new_group)
    except Exception as e:
        db.session.rollback()
        print(f"Edit student error: {e}")
        return jsonify(success=False, message="Error updating student.")

@app.route('/delete_student', methods=['POST'])
@teacher_required
def delete_student():
    """
    Handle student deletion with validation checks.
    
    Prevents deletion if student has already taken the exam.
    """
    data = request.get_json()
    student_id = data.get('id')

    if not student_id:
        return jsonify(success=False, message="Student ID is required.")

    try:
        # Find and authorize student
        student_db = db.session.get(Student, int(student_id))
        if not student_db:
            return jsonify(success=False, message="Student not found.")
        
        if student_db.teacher_id != session['teacher_id']:
            return jsonify(success=False, message="Not authorized to delete this student.")

        # Check if student has exam results
        has_result = Result.query.filter_by(student_id=student_id).first()
        if has_result:
            return jsonify(success=False, message="Cannot delete student who has already taken the exam.")

        # Delete student
        db.session.delete(student_db)
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        print(f"Delete student error: {e}")
        return jsonify(success=False, message="Error deleting student.")

@app.route('/reset_student_password', methods=['POST'])
@teacher_required
def reset_student_password():
    """
    Generate new random password for student account.
    
    Returns the new password for teacher to share with student.
    """
    data = request.get_json()
    student_id = data.get('id')

    if not student_id:
        return jsonify(success=False, message="Student ID is required.")

    try:
        # Find and authorize student
        student_db = db.session.get(Student, int(student_id))
        if not student_db:
            return jsonify(success=False, message="Student not found.")
        
        if student_db.teacher_id != session['teacher_id']:
            return jsonify(success=False, message="Not authorized to reset this student's password.")

        # Generate new password
        new_password = generate_random_password(8)
        student_db.password = generate_password_hash(new_password)
        db.session.commit()
        
        return jsonify(success=True, password=new_password)
    except Exception as e:
        db.session.rollback()
        print(f"Reset password error: {e}")
        return jsonify(success=False, message="Error resetting password.")

# ============================================================================
# FILE DOWNLOAD ROUTES
# ============================================================================

@app.route('/download_passwords_csv')
@teacher_required
def download_passwords_csv():
    """
    Download CSV file containing student passwords after bulk upload.
    
    Uses session data to provide immediate password download.
    """
    passwords_to_deliver = session.pop('passwords_to_deliver', None)
    if not passwords_to_deliver:
        flash('No passwords to deliver. Please upload students first.', 'warning')
        return redirect(url_for('teacher'))

    # Prepare CSV data
    data = [[s["ID"], s["Name"], s["Group"], s["Username"], s["Password"]] 
            for s in passwords_to_deliver]
    headers = ['ID', 'Name', 'Group', 'Username', 'Password']
    
    return create_csv_response(data, headers, "students_passwords.csv")

@app.route('/download_students_csv')
@teacher_required
def download_students_csv():
    """Download CSV file with current student list for the teacher."""
    teacher = get_teacher()
    students_list = Student.query.filter_by(teacher_id=teacher.id).all()

    data = [[s.id, s.name, s.group, s.username] for s in students_list]
    headers = ['ID', 'Name', 'Group', 'Username']
    filename = f"students_list_{teacher.username}.csv"
    
    return create_csv_response(data, headers, filename)

@app.route('/download_results_csv')
@teacher_required
def download_results_csv():
    """Download CSV file with exam results for the teacher's students."""
    teacher = get_teacher()
    results_list = Result.query.join(Student, Result.student_id == Student.id)\
        .filter(Student.teacher_id == teacher.id).all()

    data = [[r.student_id, r.name, r.group, r.mathematics, r.physics, 
             r.chemistry, r.biology, r.computer_science, r.total] 
            for r in results_list]
    headers = ['ID', 'Name', 'Group', 'Mathematics', 'Physics', 
               'Chemistry', 'Biology', 'Computer Science', 'Total']
    filename = f"results_{teacher.username}.csv"
    
    return create_csv_response(data, headers, filename)

# ============================================================================
# QUIZ GENERATION ROUTES
# ============================================================================

@app.route('/create_quiz', methods=['POST'])
@teacher_required
def create_quiz():
    """
    Create quiz using questions from the question bank.
    
    Loads questions from database based on category and difficulty level.
    """
    teacher = get_teacher()
    
    # Define available categories
    categories = {
        'math': 'Mathematics',
        'physics': 'Physics', 
        'chemistry': 'Chemistry',
        'biology': 'Biology',
        'cs': 'Computer Science'
    }
    
    # Process form data to determine requested categories
    categories_to_process = []
    for key, label in categories.items():
        num_questions_str = request.form.get(f'num_questions_{key}')
        if num_questions_str and num_questions_str.isdigit() and int(num_questions_str) > 0:
            categories_to_process.append((key, label, int(num_questions_str), request.form.get(f'level_{key}')))
    
    # Validate that at least one category is selected
    if not categories_to_process:
        msg = 'Please select at least one category with questions > 0.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message=msg)
        flash(msg, 'warning')
        return redirect(url_for('teacher'))
    
    try:
        # Clean up existing quizzes for this teacher
        existing_quizzes = Quiz.query.filter_by(teacher_id=teacher.id).all()
        for quiz in existing_quizzes:
            db.session.delete(quiz)
        db.session.commit()
        
        # Create new quiz
        new_quiz = Quiz(
            teacher_id=teacher.id,
            name=f"Quiz - {teacher.name}",
            description="Generated quiz from question bank"
        )
        db.session.add(new_quiz)
        db.session.flush()  # Get quiz ID without committing
        
        # Initialize statistics tracking
        generation_stats = {
            'from_bank': 0,
            'failed_categories': []
        }
        
        all_quiz_questions = []

        # Process each requested category
        for i, (key, label, num_q, level) in enumerate(categories_to_process):
            print(f"Processing {label}: {num_q} questions from bank at level {level}")
            
            # Load questions from database
            bank_questions = load_questions_from_bank(label, level, num_q)
            
            if not bank_questions:
                generation_stats['failed_categories'].append(f"{label} ({level})")
                print(f"No questions found in bank for {label} at level {level}")
            
            all_quiz_questions.extend(bank_questions)
            generation_stats['from_bank'] += len(bank_questions)
            
            print(f"✓ {label}: {len(bank_questions)} bank questions added.")
        
        # Validate that we have questions to create quiz
        if not all_quiz_questions:
            db.session.rollback()            
            msg = '❌ Failed to generate quiz. No questions found in the bank for the selected criteria.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=False, message=msg)
            flash(msg, 'danger')
            return redirect(url_for('teacher'))

        # Save questions to database as QuizQuestion objects
        for j, q_data in enumerate(all_quiz_questions):
            quiz_question = QuizQuestion(
                quiz_id=new_quiz.id,
                question=q_data['question'],
                option_a=q_data['options'][0],
                option_b=q_data['options'][1],
                option_c=q_data['options'][2],
                option_d=q_data['options'][3],
                correct_answer=q_data['answer'],
                category=q_data['category'],
                level=q_data['level'],
                source='BANK',
                order_index=j
            )
            db.session.add(quiz_question)

        # Commit all changes
        db.session.commit()
        
        # Generate success report
        success_msg = create_generation_report(generation_stats, generation_stats['from_bank'])
        
        print(f"✅ Quiz completed: {generation_stats['from_bank']} total questions from bank")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=True, message=success_msg)
        flash(success_msg, 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating quiz: {e}")
        msg = '❌ Error creating quiz. Please try again.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message=msg)
        flash(msg, 'danger')

    return redirect(url_for('teacher'))

@app.route('/create_ai_quiz', methods=['POST'])
@teacher_required
def create_ai_quiz():
    """
    Create quiz using AI-generated questions directly.
    
    Uses Ollama AI to generate custom questions based on category and level.
    """
    teacher = get_teacher()
    
    # Define available categories
    categories = {
        'math': 'Mathematics',
        'physics': 'Physics', 
        'chemistry': 'Chemistry',
        'biology': 'Biology',
        'cs': 'Computer Science'
    }
    
    # Process form data for AI generation
    categories_to_process = []
    for key, label in categories.items():
        num_questions_str = request.form.get(f'ai_num_questions_{key}')
        if num_questions_str and num_questions_str.isdigit() and int(num_questions_str) > 0:
            level = request.form.get(f'ai_level_{key}')
            categories_to_process.append((label, level, int(num_questions_str)))
    
    # Validate that at least one category is selected
    if not categories_to_process:
        msg = 'Please select at least one category with questions > 0 for AI generation.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message=msg)
        flash(msg, 'warning')
        return redirect(url_for('teacher'))
    
    try:
        # Initialize AI Quiz Generator
        ai_generator = QuizGenerator()
        
        # Check Ollama connection before proceeding
        if not ai_generator.check_ollama_connection():
            msg = '❌ Cannot connect to Ollama. Please make sure Ollama is running and try again.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=False, message=msg)
            flash(msg, 'danger')
            return redirect(url_for('teacher'))
        
        # Clean up existing quizzes
        existing_quizzes = Quiz.query.filter_by(teacher_id=teacher.id).all()
        for quiz in existing_quizzes:
            db.session.delete(quiz)
        db.session.commit()
        
        # Create new quiz
        new_quiz = Quiz(
            teacher_id=teacher.id,
            name=f"AI Quiz - {teacher.name}",
            description="Generated quiz using AI"
        )
        db.session.add(new_quiz)
        db.session.flush()  # Get the quiz ID
        
        # Generate questions using AI
        temp_csv_path = ai_generator.generate_and_save_temp_csv(categories_to_process)
        
        # Parse CSV and convert to QuizQuestion objects
        ai_quiz_questions = parse_ai_csv_to_quiz_questions(temp_csv_path, new_quiz.id)
        
        # Add AI questions to database
        for quiz_question in ai_quiz_questions:
            db.session.add(quiz_question)
        
        db.session.commit()
        
        # Create success message
        success_msg = f"""✅ <strong>AI Quiz Created Successfully!</strong><br><br>
                        🤖 <strong>AI Generation Report:</strong><br>
                        📝 Generated Questions: <strong>{len(ai_quiz_questions)}</strong><br>
                        🎯 Quiz is ready for students to take<br>
                        💡 Questions were generated directly for your quiz."""
        
        print(f"✅ AI Quiz completed: {len(ai_quiz_questions)} questions generated")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=True, message=success_msg)
        flash(success_msg, 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating AI quiz: {e}")
        msg = f'❌ Error generating AI quiz: {str(e)}'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message=msg)
        flash(msg, 'danger')

    return redirect(url_for('teacher'))

@app.route('/create_unified_quiz', methods=['POST'])
@teacher_required
def create_unified_quiz():
    """
    Create quiz using both AI-generated questions and question bank.
    
    Allows mixing of questions from database and AI generation
    based on user's checkbox selections for each category.
    """
    teacher = get_teacher()
    
    # Define available categories
    categories = {
        'math': 'Mathematics',
        'physics': 'Physics', 
        'chemistry': 'Chemistry',
        'biology': 'Biology',
        'cs': 'Computer Science'
    }
    
    # Analyze form data to determine source for each category
    ai_categories = []
    bank_categories = []
    
    for key, label in categories.items():
        num_questions_str = request.form.get(f'num_questions_{key}')
        use_ai = request.form.get(f'use_ai_{key}') == 'on'
        level = request.form.get(f'level_{key}')
        
        if num_questions_str and num_questions_str.isdigit() and int(num_questions_str) > 0:
            num_questions = int(num_questions_str)
            
            if use_ai:
                ai_categories.append((label, level, num_questions))
                print(f"AI Category: {label}, Level: {level}, Questions: {num_questions}")
            else:
                bank_categories.append((key, label, num_questions, level))
                print(f"Bank Category: {label}, Level: {level}, Questions: {num_questions}")
    
    # Validate that at least one category is selected
    if not ai_categories and not bank_categories:
        msg = 'Please select at least one category with questions > 0.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message=msg)
        flash(msg, 'warning')
        return redirect(url_for('teacher'))
    
    try:
        # Step 1: Clean up existing quizzes
        existing_quizzes = Quiz.query.filter_by(teacher_id=teacher.id).all()
        for quiz in existing_quizzes:
            db.session.delete(quiz)
        db.session.commit()
        
        # Create new quiz
        new_quiz = Quiz(
            teacher_id=teacher.id,
            name=f"Quiz - {teacher.name}",
            description="Generated quiz with mixed sources"
        )
        db.session.add(new_quiz)
        db.session.flush()  # Get the quiz ID
        
        # Initialize statistics tracking
        generation_stats = {
            'from_ai': 0,
            'from_bank': 0,
            'failed_categories': []
        }
        
        # Step 2: Handle AI generation if requested
        if ai_categories:
            print("Processing AI categories...")
            
            # Initialize AI Quiz Generator
            ai_generator = QuizGenerator()
            
            # Check Ollama connection
            if not ai_generator.check_ollama_connection():
                raise Exception('Cannot connect to Ollama. Make sure it is running on localhost:11434')
            
            # Generate AI questions and save to temporary CSV
            temp_csv_path = ai_generator.generate_and_save_temp_csv(ai_categories)
            
            # Parse CSV and convert to QuizQuestion objects
            ai_quiz_questions = parse_ai_csv_to_quiz_questions(temp_csv_path, new_quiz.id)
            
            # Add AI questions to database
            for quiz_question in ai_quiz_questions:
                db.session.add(quiz_question)
            
            generation_stats['from_ai'] = len(ai_quiz_questions)
            print(f"Added {len(ai_quiz_questions)} AI questions to quiz")
        
        # Step 3: Handle Bank questions if requested
        if bank_categories:
            print("Processing Bank categories...")
            for i, (key, label, num_q, level) in enumerate(bank_categories):
                print(f"Loading {num_q} questions for {label} at {level} level from bank")
                bank_questions = load_questions_from_bank(label, level, num_q)
                
                if not bank_questions:
                    generation_stats['failed_categories'].append(f"{label} ({level})")
                    print(f"No questions found for {label} at {level} level")
                else:
                    # Convert bank questions to QuizQuestion objects
                    for j, q_data in enumerate(bank_questions):
                        quiz_question = QuizQuestion(
                            quiz_id=new_quiz.id,
                            question=q_data['question'],
                            option_a=q_data['options'][0],
                            option_b=q_data['options'][1],
                            option_c=q_data['options'][2],
                            option_d=q_data['options'][3],
                            correct_answer=q_data['answer'],
                            category=q_data['category'],
                            level=q_data['level'],
                            source='BANK',
                            order_index=generation_stats['from_ai'] + generation_stats['from_bank'] + j
                        )
                        db.session.add(quiz_question)
                    
                    generation_stats['from_bank'] += len(bank_questions)
                    print(f"Added {len(bank_questions)} bank questions for {label}")
        
        # Step 4: Finalize quiz creation
        total_questions = generation_stats['from_ai'] + generation_stats['from_bank']
        print(f"Total questions in quiz: {total_questions}")
        
        # Validate that we have questions to create quiz
        if total_questions == 0:
            db.session.rollback()
            raise Exception('Failed to load any questions. No questions found for the selected criteria.')

        # Commit all changes to database
        db.session.commit()
        
        # Generate detailed success message
        success_msg = create_generation_report(generation_stats, total_questions)
        
        print(f"✅ Unified quiz completed: {total_questions} total questions")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=True, message=success_msg)
        flash(success_msg, 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating unified quiz: {e}")
        msg = f'❌ Error creating quiz: {str(e)}'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message=msg)
        flash(msg, 'danger')

    return redirect(url_for('teacher'))

# ============================================================================
# QUIZ MANAGEMENT ROUTES
# ============================================================================

@app.route('/exam_teacher')
@teacher_required
def exam_teacher():
    """
    Display quiz preview for teacher.
    
    Shows the current active quiz with all questions for teacher review.
    """
    teacher = get_teacher()
    
    # Get active quiz from database
    quiz = Quiz.query.filter_by(teacher_id=teacher.id, is_active=True).first()
    quiz_questions = []
    
    if quiz:
        quiz_questions = [q.to_dict() for q in quiz.questions]
    
    return render_template('exam_teacher.html', 
                         teacher_name=teacher.name, 
                         quiz_questions=quiz_questions)

@app.route('/delete_quiz', methods=['POST'])
@teacher_required
def delete_quiz():
    """
    Delete all quizzes for the current teacher.
    
    Removes all quiz data including questions and resets quiz state.
    """
    teacher = get_teacher()
    
    try:
        quizzes = Quiz.query.filter_by(teacher_id=teacher.id).all()
        
        if quizzes:
            deleted_count = len(quizzes)
            for quiz in quizzes:
                db.session.delete(quiz)
            
            db.session.commit()
            
            message = f"Successfully deleted {deleted_count} quiz(es)! 🗑️"
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=True, message=message)
            
            flash(message, 'success')
        else:
            message = "No quizzes found to delete."
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=False, message=message)
            
            flash(message, 'warning')
            
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting quiz: {e}")
        
        message = "Error deleting quiz. Please try again."
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message=message)
        
        flash(message, 'danger')

    return redirect(url_for('teacher'))

@app.route('/reset_student_result', methods=['POST'])
@teacher_required
def reset_student_result():
    """
    Reset student exam result to allow retaking.
    
    Removes the student's quiz result, enabling them to take the quiz again.
    """
    data = request.get_json()
    student_id = data.get('id')

    if not student_id:
        return jsonify(success=False, message="Student ID is required.")

    try:
        result_db = Result.query.filter_by(student_id=int(student_id)).first()
        if result_db:
            db.session.delete(result_db)
            db.session.commit()
            return jsonify(success=True)
        return jsonify(success=False, message="Result not found.")
    except Exception as e:
        db.session.rollback()
        print(f"Reset result error: {e}")
        return jsonify(success=False, message="Error resetting result.")

# ============================================================================
# STUDENT ROUTES
# ============================================================================

@app.route('/student')
@student_required
def student():
    """
    Student dashboard.
    
    Main page for students showing their information and teacher details.
    """
    student = get_student()
    teacher = db.session.get(Teacher, student.teacher_id) if student else None
    
    return render_template(
        'student.html',
        student_name=student.name,
        teacher_name=teacher.name if teacher else "Unknown"
    )

@app.route('/quiz')
@student_required
def quiz():
    """
    Display quiz for student to take.
    
    Shows quiz questions if available and not already completed,
    or displays results if already taken.
    """
    student = get_student()
    teacher = db.session.get(Teacher, student.teacher_id) if student else None
    quiz_questions = []
    already_done = False
    student_result = None

    if teacher:
        # Check if student has already completed the quiz
        result_db = Result.query.filter_by(student_id=student.id).first()
        if result_db:
            already_done = True
            student_result = {
                "mathematics": result_db.mathematics,
                "physics": result_db.physics,
                "chemistry": result_db.chemistry,
                "biology": result_db.biology,
                "computer_science": result_db.computer_science,
                "total": result_db.total
            }
        else:
            # Load quiz questions from database
            quiz = Quiz.query.filter_by(teacher_id=teacher.id, is_active=True).first()
            if quiz:
                quiz_questions = [q.to_dict() for q in quiz.questions]

    return render_template(
        'quiz.html',
        student_name=student.name,
        teacher_name=teacher.name if teacher else "Unknown",
        quiz_questions=quiz_questions,
        already_done=already_done,
        student_result=student_result
    )

@app.route('/submit_quiz', methods=['POST'])
@student_required
def submit_quiz():
    """
    Handle quiz submission and scoring.
    
    Processes student answers, calculates scores by category,
    and saves results to database.
    """
    student = get_student()
    teacher = db.session.get(Teacher, student.teacher_id) if student else None
    
    if not teacher:
        return jsonify(success=False, message="Teacher not found.")

    # Check if student has already completed the quiz
    existing_result = Result.query.filter_by(student_id=student.id).first()
    if existing_result:
        return jsonify(success=False, message="You have already completed this quiz. You cannot retake it.")

    # Load quiz questions from database
    quiz = Quiz.query.filter_by(teacher_id=teacher.id, is_active=True).first()
    if not quiz:
        return jsonify(success=False, message="Quiz not found.")
    
    quiz_questions = [q.to_dict() for q in quiz.questions]

    try:
        # Process answers and calculate scores by category
        scores = calculate_quiz_scores(quiz_questions, request.form)
        
        # Save results to database
        result_data = create_result_data(student, scores)
        new_result = Result(**result_data)
        db.session.add(new_result)
        db.session.commit()

        # Generate summary for display
        summary = format_result_summary(result_data)
        return jsonify(success=True, 
                      message="Quiz submitted successfully! 🎉", 
                      summary=summary)

    except Exception as e:
        db.session.rollback()
        print(f"Quiz submission error: {e}")
        return jsonify(success=False, message="Error submitting quiz. Please try again.")

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
