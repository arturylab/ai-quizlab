import csv
import random
import string
import os
import json
import io
import time
from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify, flash
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash
from datetime import timedelta
from config import Config
from models import db, Teacher, Student, Result, QuestionBank, Quiz, QuizQuestion
from functools import wraps

app = Flask(__name__)
app.config.from_object(Config)
app.permanent_session_lifetime = timedelta(minutes=30)

# Initialize database and migrations
db.init_app(app)
migrate = Migrate(app, db)

# ---------- DECORATORS ---------- #

def teacher_required(f):
    """Decorator to ensure user is logged in as a teacher."""
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
    """Decorator to ensure user is logged in as a student."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'student_id' not in session:
            if request.is_json:
                return jsonify(success=False, message="Student authentication required")
            flash('Please log in as a student to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ---------- UTILITY FUNCTIONS ---------- #

def get_teacher():
    """Return the current logged-in teacher object."""
    teacher_id = session.get('teacher_id')
    if teacher_id:
        return db.session.get(Teacher, teacher_id)
    return None

def get_student():
    """Return the current logged-in student object."""
    student_id = session.get('student_id')
    if student_id:
        return db.session.get(Student, student_id)
    return None

def get_json_path(folder, filename):
    """Return the full path for a JSON file in a given folder."""
    return os.path.join(folder, filename)

def read_json(path):
    """Read and return JSON data from a file, or an empty list if not found."""
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading JSON file {path}: {e}")
    return []

def write_json(path, data):
    """Write data to a JSON file with error handling."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except IOError as e:
        print(f"Error writing JSON file {path}: {e}")
        raise

def generate_random_password(length=8):
    """Generate a secure random password with letters and digits."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def create_csv_response(data, headers, filename):
    """Create a CSV response for file download."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(data)
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

def validate_form_data(data, required_fields):
    """Validate form data and return errors if any."""
    errors = []
    for field in required_fields:
        if not data.get(field, '').strip():
            errors.append(f"{field.title()} is required.")
    return errors

# ---------- ROUTES ---------- #

# ---------- Authentication Routes ---------- #

@app.route('/')
def index():
    """Redirect to login page."""
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login for both teachers and students."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Validate input
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('login.html')

        # Try teacher login first
        teacher = Teacher.query.filter_by(username=username).first()
        if teacher and teacher.check_password(password):
            session['teacher_id'] = teacher.id
            session.permanent = True
            flash('Login successful! Welcome, teacher.', 'success')
            return redirect(url_for('teacher'))

        # Try student login
        student = Student.query.filter_by(username=username).first()
        if student and student.check_password(password):
            session['student_id'] = student.id
            session.permanent = True
            flash('Login successful! Welcome, student.', 'success')
            return redirect(url_for('student'))

        # Invalid credentials
        flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    """Handle user logout and clear session."""
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle teacher registration."""
    if request.method == 'POST':
        # Extract form data
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

        # Create new teacher
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

# ---------- Teacher Routes ---------- #

@app.route('/teacher')
@teacher_required
def teacher():
    """Teacher dashboard showing students and results."""
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
    """Handle teacher profile management."""
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

# ---------- Student Management Routes ---------- #

@app.route('/upload', methods=['POST'])
@teacher_required
def upload_students():
    """Handle CSV upload for student registration."""
    file = request.files.get('file')
    if not file or not file.filename.endswith('.csv'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message='Invalid file. Please upload a CSV file.')
        flash('Invalid file. Please upload a CSV file.', 'danger')
        return redirect(url_for('teacher'))

    try:
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

            # Validation
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
            db.session.flush()  # Get the ID

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

        db.session.commit()
        session['passwords_to_deliver'] = passwords_to_deliver

        # Handle AJAX request
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
    """Handle student information editing."""
    data = request.get_json()
    student_id = data.get('id')
    new_name = data.get('name', '').strip()
    new_group = data.get('group', '').strip()

    # Validation
    if not student_id or not new_name or not new_group:
        return jsonify(success=False, message="All fields are required.")

    try:
        student_db = db.session.get(Student, int(student_id))
        if not student_db:
            return jsonify(success=False, message="Student not found.")
        
        if student_db.teacher_id != session['teacher_id']:
            return jsonify(success=False, message="Not authorized to edit this student.")

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
    """Handle student deletion with validation."""
    data = request.get_json()
    student_id = data.get('id')

    if not student_id:
        return jsonify(success=False, message="Student ID is required.")

    try:
        student_db = db.session.get(Student, int(student_id))
        if not student_db:
            return jsonify(success=False, message="Student not found.")
        
        if student_db.teacher_id != session['teacher_id']:
            return jsonify(success=False, message="Not authorized to delete this student.")

        # Check if student has taken any exams
        has_result = Result.query.filter_by(student_id=student_id).first()
        if has_result:
            return jsonify(success=False, message="Cannot delete student who has already taken the exam.")

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
    """Reset student password and return new password."""
    data = request.get_json()
    student_id = data.get('id')

    if not student_id:
        return jsonify(success=False, message="Student ID is required.")

    try:
        student_db = db.session.get(Student, int(student_id))
        if not student_db:
            return jsonify(success=False, message="Student not found.")
        
        if student_db.teacher_id != session['teacher_id']:
            return jsonify(success=False, message="Not authorized to reset this student's password.")

        new_password = generate_random_password(8)
        student_db.password = generate_password_hash(new_password)
        db.session.commit()
        
        return jsonify(success=True, password=new_password)
    except Exception as e:
        db.session.rollback()
        print(f"Reset password error: {e}")
        return jsonify(success=False, message="Error resetting password.")

# ---------- File Download Routes ---------- #

@app.route('/download_passwords_csv')
@teacher_required
def download_passwords_csv():
    """Download CSV file with student passwords."""
    passwords_to_deliver = session.pop('passwords_to_deliver', None)
    if not passwords_to_deliver:
        flash('No passwords to deliver. Please upload students first.', 'warning')
        return redirect(url_for('teacher'))

    data = [[s["ID"], s["Name"], s["Group"], s["Username"], s["Password"]] 
            for s in passwords_to_deliver]
    headers = ['ID', 'Name', 'Group', 'Username', 'Password']
    
    return create_csv_response(data, headers, "students_passwords.csv")

@app.route('/download_students_csv')
@teacher_required
def download_students_csv():
    """Download CSV file with student list."""
    teacher = get_teacher()
    students_list = Student.query.filter_by(teacher_id=teacher.id).all()

    data = [[s.id, s.name, s.group, s.username] for s in students_list]
    headers = ['ID', 'Name', 'Group', 'Username']
    filename = f"students_list_{teacher.username}.csv"
    
    return create_csv_response(data, headers, filename)

@app.route('/download_results_csv')
@teacher_required
def download_results_csv():
    """Download CSV file with exam results."""
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

# ---------- Quiz Management Routes ---------- #

# Global variable to track progress
quiz_progress = {
    'current': 0,
    'total': 0,
    'status': 'idle',
    'message': '',
    'teacher_id': None
}

@app.route('/quiz_progress')
@teacher_required
def get_quiz_progress():
    """Get current quiz generation progress."""
    teacher = get_teacher()
    if quiz_progress['teacher_id'] == teacher.id:
        return jsonify({
            'progress': quiz_progress['current'],
            'total': quiz_progress['total'],
            'status': quiz_progress['status'],
            'message': quiz_progress['message'],
            'percentage': int((quiz_progress['current'] / quiz_progress['total'] * 100)) if quiz_progress['total'] > 0 else 0
        })
    else:
        return jsonify({
            'progress': 0,
            'total': 0,
            'status': 'idle',
            'message': '',
            'percentage': 0
        })

@app.route('/create_quiz', methods=['POST'])
@teacher_required
def create_quiz():
    """Create quiz using questions from the question bank."""
    global quiz_progress
    teacher = get_teacher()
    
    categories = {
        'math': 'Mathematics',
        'physics': 'Physics', 
        'chemistry': 'Chemistry',
        'biology': 'Biology',
        'cs': 'Computer Science'
    }
    
    categories_to_process = []
    for key, label in categories.items():
        num_questions_str = request.form.get(f'num_questions_{key}')
        if num_questions_str and num_questions_str.isdigit() and int(num_questions_str) > 0:
            categories_to_process.append((key, label, int(num_questions_str), request.form.get(f'level_{key}')))
    
    if not categories_to_process:
        msg = 'Please select at least one category with questions > 0.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message=msg)
        flash(msg, 'warning')
        return redirect(url_for('teacher'))
    
    quiz_progress.update({
        'current': 0,
        'total': len(categories_to_process),
        'status': 'processing',
        'message': 'Starting quiz generation...',
        'teacher_id': teacher.id
    })
    
    try:
        existing_quiz = Quiz.query.filter_by(teacher_id=teacher.id, is_active=True).first()
        if existing_quiz:
            existing_quiz.is_active = False
            db.session.commit()
        
        new_quiz = Quiz(
            teacher_id=teacher.id,
            name=f"Quiz - {teacher.name}",
            description="Generated quiz from question bank"
        )
        db.session.add(new_quiz)
        db.session.flush()
        
        generation_stats = {
            'from_bank': 0,
            'failed_categories': []
        }
        
        all_quiz_questions = []

        for i, (key, label, num_q, level) in enumerate(categories_to_process):
            quiz_progress.update({
                'current': i,
                'message': f'Processing {label}... ({i+1}/{len(categories_to_process)})'
            })
            
            print(f"Processing {label}: {num_q} questions from bank at level {level}")
            
            bank_questions = load_questions_from_bank(label, level, num_q)
            
            if not bank_questions:
                generation_stats['failed_categories'].append(f"{label} ({level})")
                print(f"No questions found in bank for {label} at level {level}")
                # Continue to next category if no questions found for this one
                # If you want to fail the entire quiz generation, you can add a check here
                # and rollback / return error.
                # For now, we'll just skip this category.
                # continue # Optional: skip if no questions
            
            all_quiz_questions.extend(bank_questions)
            generation_stats['from_bank'] += len(bank_questions)
            
            print(f"✓ {label}: {len(bank_questions)} bank questions added.")
            time.sleep(0.1) # Shorter sleep as DB access is faster
        
        if not all_quiz_questions: # Check if any questions were added at all
            db.session.rollback()
            quiz_progress.update({
                'status': 'error',
                'message': 'Failed to load any questions from the bank.'
            })
            
            msg = '❌ Failed to generate quiz. No questions found in the bank for the selected criteria.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=False, message=msg)
            flash(msg, 'danger')
            return redirect(url_for('teacher'))

        # Save QuizQuestions to the database
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
                source='BANK', # Source is now always BANK
                order_index=j
            )
            db.session.add(quiz_question)

        db.session.commit()
        
        quiz_progress.update({
            'current': len(categories_to_process),
            'status': 'completed',
            'message': 'Quiz generated successfully from bank!'
        })
        
        success_msg = create_generation_report(generation_stats, generation_stats['from_bank'])
        
        print(f"✅ Quiz completed: {generation_stats['from_bank']} total questions from bank")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=True, message=success_msg)
        flash(success_msg, 'success')
        
    except Exception as e:
        db.session.rollback()
        quiz_progress.update({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        })
        print(f"Error creating quiz: {e}")
        msg = '❌ Error creating quiz. Please try again.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message=msg)
        flash(msg, 'danger')

    return redirect(url_for('teacher'))

def load_questions_from_bank(subject, level, num_needed):
    """Load questions from the QuestionBank table in the database."""
    import random
    
    try:
        # Query the QuestionBank table
        # Ensure 'subject' and 'level' parameters match the values in your QuestionBank table
        # For example, if your table stores 'Mathematics' as subject, pass that directly.
        # If your table uses different casing or naming, adjust here or in the calling function.
        
        # Fetch all matching questions first
        all_matching_questions = QuestionBank.query.filter_by(
            category=subject, 
            level=level
        ).all()
        
        if not all_matching_questions:
            print(f"No questions found in DB for {subject} - {level}")
            return []

        # Shuffle them to get a random selection
        random.shuffle(all_matching_questions)
        
        # Select the number needed
        selected_db_questions = all_matching_questions[:num_needed]
        
        formatted_questions = []
        for i, db_q in enumerate(selected_db_questions):
            # Adapt this mapping based on your QuestionBank model fields
            formatted_q = {
                'id': f"BANK-{db_q.id}", # Or use db_q.id directly if preferred
                'question': db_q.question, # CAMBIADO DE db_q.question_text
                'options': [
                    db_q.option_a, 
                    db_q.option_b, 
                    db_q.option_c, 
                    db_q.option_d
                ], # Assuming these field names
                'answer': db_q.correct_answer, # Assuming field name
                'category': db_q.category,
                'level': db_q.level,
                'source': 'BANK' # Source is always BANK now
            }
            formatted_questions.append(formatted_q)
        
        print(f"Loaded {len(formatted_questions)} questions from DB for {subject} - {level}")
        return formatted_questions
        
    except Exception as e:
        print(f"Error loading questions from database bank: {e}")
        # Consider how to handle DB errors, e.g., logging, re-raising
    
    return []

def create_generation_report(stats, total_questions):
    """Create detailed generation report (simplified for bank-only)."""
    bank_count = stats['from_bank']
    failed = stats.get('failed_categories', []) # Ensure 'failed_categories' key exists
    
    # Calculate percentages
    bank_percent = 100 if total_questions > 0 else 0 # Simplified as all are from bank
    
    report = f"""✅ <strong>Quiz Generated Successfully!</strong><br><br>
📊 <strong>Generation Report:</strong><br>
📚 From Bank: <strong>{bank_count}</strong> questions ({bank_percent}%)<br>
📝 Total Questions: <strong>{total_questions}</strong><br>"""
    
    if failed:
        report += f"<br>⚠️ Categories with no questions found: {', '.join(failed)}"
    
    return report
# ---------- Exam Management Routes ---------- #

@app.route('/exam_teacher')
@teacher_required
def exam_teacher():
    """Display quiz preview for teacher."""
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
    """Delete the generated quiz for the current teacher."""
    teacher = get_teacher()
    
    try:
        # Find and delete quiz
        quiz = Quiz.query.filter_by(teacher_id=teacher.id, is_active=True).first()
        
        if quiz:
            db.session.delete(quiz)  # Cascade will delete QuizQuestions
            db.session.commit()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=True, message="Quiz deleted successfully! 🗑️")
            
            flash('Quiz deleted successfully! 🗑️', 'success')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=False, message="No quiz found to delete.")
            
            flash('No quiz found to delete.', 'warning')
            
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting quiz: {e}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message="Error deleting quiz. Please try again.")
        
        flash('Error deleting quiz. Please try again.', 'danger')

    return redirect(url_for('teacher'))

@app.route('/reset_student_result', methods=['POST'])
@teacher_required
def reset_student_result():
    """Reset student exam result."""
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

# ---------- Student Routes ---------- #

@app.route('/student')
@student_required
def student():
    """Student dashboard."""
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
    """Display quiz for student to take."""
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
    """Handle quiz submission and scoring."""
    student = get_student()
    teacher = db.session.get(Teacher, student.teacher_id) if student else None
    
    if not teacher:
        return jsonify(success=False, message="Teacher not found.")

    # Check if already completed
    existing_result = Result.query.filter_by(student_id=student.id).first()
    if existing_result:
        return jsonify(success=False, message="You have already completed this quiz. You cannot retake it.")

    # Load quiz questions from database
    quiz = Quiz.query.filter_by(teacher_id=teacher.id, is_active=True).first()
    if not quiz:
        return jsonify(success=False, message="Quiz not found.")
    
    quiz_questions = [q.to_dict() for q in quiz.questions]

    try:
        # Process answers and calculate scores
        scores = calculate_quiz_scores(quiz_questions, request.form)
        
        # Save to database only
        result_data = create_result_data(student, scores)
        new_result = Result(**result_data)
        db.session.add(new_result)
        db.session.commit()

        summary = format_result_summary(result_data)
        return jsonify(success=True, 
                      message="Quiz submitted successfully! 🎉", 
                      summary=summary)

    except Exception as e:
        db.session.rollback()
        print(f"Quiz submission error: {e}")
        return jsonify(success=False, message="Error submitting quiz. Please try again.")

# ---------- Helper Functions for Quiz Processing ---------- #

def calculate_quiz_scores(quiz_questions, form_data):
    """Calculate scores for each category based on quiz answers."""
    categories = {
        'Mathematics': {'correct': 0, 'total': 0},
        'Physics': {'correct': 0, 'total': 0},
        'Chemistry': {'correct': 0, 'total': 0},
        'Biology': {'correct': 0, 'total': 0},
        'Computer Science': {'correct': 0, 'total': 0}
    }
    
    total_correct = 0
    
    for i, question in enumerate(quiz_questions):
        user_answer = form_data.get(f'q{i}')
        category = question.get('category', 'N/A')
        correct_answer = question.get('answer')
        
        if category in categories:
            categories[category]['total'] += 1
            if user_answer == correct_answer:
                categories[category]['correct'] += 1
                total_correct += 1
    
    return {
        'categories': categories,
        'total_correct': total_correct,
        'total_questions': len(quiz_questions)
    }

def create_result_data(student, scores):
    """Create result data dictionary for database storage."""
    categories = scores['categories']
    return {
        'student_id': student.id,
        'name': student.name,
        'group': student.group,
        'mathematics': f"{categories['Mathematics']['correct']}/{categories['Mathematics']['total']}",
        'physics': f"{categories['Physics']['correct']}/{categories['Physics']['total']}",
        'chemistry': f"{categories['Chemistry']['correct']}/{categories['Chemistry']['total']}",
        'biology': f"{categories['Biology']['correct']}/{categories['Biology']['total']}",
        'computer_science': f"{categories['Computer Science']['correct']}/{categories['Computer Science']['total']}",
        'total': f"{scores['total_correct']}/{scores['total_questions']}"
    }

def format_result_summary(result_data):
    """Format result summary for display."""
    return f"""
    <b>Results Summary:</b><br>
    Mathematics: {result_data['mathematics']}<br>
    Physics: {result_data['physics']}<br>
    Chemistry: {result_data['chemistry']}<br>
    Biology: {result_data['biology']}<br>
    Computer Science: {result_data['computer_science']}<br>
    <b>Total: {result_data['total']}</b>
    """

# ---------- Application Initialization ---------- #

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
