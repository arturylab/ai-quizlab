from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify, flash
from werkzeug.security import generate_password_hash
from datetime import timedelta
from config import Config
from models import db, Teacher, Student, Result
import csv
import random
import string
import os
import json
import io

app = Flask(__name__)
app.config.from_object(Config)
app.permanent_session_lifetime = timedelta(minutes=30)
db.init_app(app)

# ---------- Utility Functions ----------

def get_teacher():
    """Return the current logged-in teacher object."""
    return Teacher.query.get(session['teacher_id'])

def get_student():
    """Return the current logged-in student object."""
    return Student.query.get(session['student_id'])

def get_json_path(folder, filename):
    """Return the full path for a JSON file in a given folder."""
    return os.path.join(folder, filename)

def read_json(path):
    """Read and return JSON data from a file, or an empty list if not found."""
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def write_json(path, data):
    """Write data to a JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def generate_random_password(length=8):
    """Generate a random password with letters and digits."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# ---------- Routes ----------

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Try teacher login
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
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('teacher_id', None)
    session.pop('student_id', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        school = request.form['school']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        if Teacher.query.filter_by(username=username).first():
            flash('Username already exists. Please choose another.', 'danger')
            return render_template('register.html')

        if Teacher.query.filter_by(email=email).first():
            flash('Email already registered. Please use another.', 'danger')
            return render_template('register.html')

        new_teacher = Teacher(
            name=name,
            email=email,
            school=school,
            username=username,
            password=generate_password_hash(password)
        )
        db.session.add(new_teacher)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/teacher')
def teacher():
    if 'teacher_id' not in session:
        return redirect(url_for('login'))
    teacher = get_teacher()
    # Get students from DB
    students_list = Student.query.filter_by(teacher_id=teacher.id).all()
    # Get results from DB
    results_list = Result.query.join(Student, Result.student_id == Student.id)\
        .filter(Student.teacher_id == teacher.id).all()
    return render_template(
        'teacher.html',
        teacher_name=teacher.name,
        students_list=students_list,
        results_list=results_list
    )

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'teacher_id' not in session:
        return redirect(url_for('login'))
    teacher = get_teacher()

    if request.method == 'POST':
        name = request.form.get('name', teacher.name)
        school = request.form.get('school', teacher.school)
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if name and name != teacher.name:
            teacher.name = name
        if school and school != teacher.school:
            teacher.school = school
        if password:
            if password != confirm_password:
                return render_template('profile.html', teacher=teacher)
            teacher.password = generate_password_hash(password)

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', teacher=teacher)

@app.route('/upload', methods=['POST'])
def upload_students():
    if 'teacher_id' not in session:
        return redirect(url_for('login'))

    file = request.files.get('file')
    if not file or not file.filename.endswith('.csv'):
        flash('Invalid file. Please upload a CSV file.', 'danger')
        return redirect(url_for('teacher'))

    csvfile = file.stream.read().decode('utf-8').splitlines()
    reader = csv.DictReader(csvfile)
    passwords_to_deliver = []
    errors = []

    for idx, row in enumerate(reader, start=2):  # start=2 for line number (header is line 1)
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
        db.session.flush()

        passwords_to_deliver.append({
            "ID": student.id,
            "Name": name,
            "Group": group,
            "Username": username,
            "Password": password_plain
        })

    db.session.commit()
    session['passwords_to_deliver'] = passwords_to_deliver

    if errors:
        flash('Some students were not added:\n' + '\n'.join(errors), 'warning')

    return redirect(url_for('download_passwords_csv'))

@app.route('/download_students_csv')
def download_students_csv():
    if 'teacher_id' not in session:
        return redirect(url_for('login'))
    teacher = get_teacher()
    # Get all students for this teacher from the database
    students_list = Student.query.filter_by(teacher_id=teacher.id).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Group', 'Username'])
    for student in students_list:
        writer.writerow([
            student.id,
            student.name,
            student.group,
            student.username
        ])
    output.seek(0)
    filename = f"students_list_{teacher.username}.csv"
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@app.route('/create_quiz', methods=['POST'])
def create_quiz():
    if 'teacher_id' not in session:
        msg = 'You must be logged in as a teacher.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message=msg)
        return redirect(url_for('login'))

    teacher = get_teacher()
    categories = {
        'math': 'Mathematics',
        'physics': 'Physics',
        'chemistry': 'Chemistry',
        'biology': 'Biology',
        'cs': 'Computer Science'
    }
    quiz_questions = []

    for key, label in categories.items():
        num_questions = request.form.get(f'num_questions_{key}')
        level = request.form.get(f'level_{key}')
        if num_questions and int(num_questions) > 0:
            level_folder = level.lower().replace(' ', '_')
            file_key = 'computerscience' if key == 'cs' else key
            # Updated path for precreated exams
            exam_path = os.path.join('data', 'exams', 'precreated', level_folder, f'{file_key}.json')
            if os.path.exists(exam_path):
                with open(exam_path, 'r', encoding='utf-8') as f:
                    questions = json.load(f)
                random.shuffle(questions)
                quiz_questions.extend(questions[:int(num_questions)])

    if not quiz_questions:
        msg = 'No questions selected. Please specify at least one category and number of questions.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message=msg)
        return redirect(url_for('teacher'))

    # Updated path for generated exams
    generated_dir = os.path.join('data', 'exams', 'generated')
    os.makedirs(generated_dir, exist_ok=True)
    quiz_filename = f'quiz_{teacher.username}.json'
    quiz_path = os.path.join(generated_dir, quiz_filename)
    with open(quiz_path, 'w', encoding='utf-8') as f:
        json.dump(quiz_questions, f, ensure_ascii=False, indent=4)

    msg = f'Quiz 📝 generated successfully! 😃'
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(success=True, message=msg)
    return redirect(url_for('teacher'))

@app.route('/exam_teacher')
def exam_teacher():
    if 'teacher_id' not in session:
        return redirect(url_for('login'))
    teacher = get_teacher()
    # Updated path for generated exams
    quiz_path = os.path.join('data', 'exams', 'generated', f'quiz_{teacher.username}.json')
    quiz_questions = []
    if os.path.exists(quiz_path):
        with open(quiz_path, 'r', encoding='utf-8') as f:
            quiz_questions = json.load(f)
    return render_template('exam_teacher.html', teacher_name=teacher.name, quiz_questions=quiz_questions)

@app.route('/student')
def student():
    if 'student_id' not in session:
        return redirect(url_for('login'))
    student = get_student()
    teacher = Teacher.query.get(student.teacher_id) if student else None
    return render_template(
        'student.html',
        student_name=student.name,
        teacher_name=teacher.name if teacher else "Unknown"
    )

@app.route('/quiz')
def quiz():
    if 'student_id' not in session:
        return redirect(url_for('login'))
    student = get_student()
    teacher = Teacher.query.get(student.teacher_id) if student else None
    quiz_questions = []
    already_done = False
    student_result = None

    if teacher:
        results_path = get_json_path('data/results', f'{teacher.username}.json')
        results_data = read_json(results_path)
        for result in results_data:
            if result.get("student_id") == student.id:
                already_done = True
                student_result = result
                break

        if not already_done:
            # Updated path for generated exams
            quiz_path = os.path.join('data', 'exams', 'generated', f'quiz_{teacher.username}.json')
            if os.path.exists(quiz_path):
                with open(quiz_path, 'r', encoding='utf-8') as f:
                    quiz_questions = json.load(f)

    return render_template(
        'quiz.html',
        student_name=student.name,
        teacher_name=teacher.name if teacher else "Unknown",
        quiz_questions=quiz_questions,
        already_done=already_done,
        student_result=student_result
    )

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if 'student_id' not in session:
        return jsonify(success=False, message="Session expired. Please log in again.")

    student = get_student()
    teacher = Teacher.query.get(student.teacher_id) if student else None
    if not teacher:
        return jsonify(success=False, message="Teacher not found.")

    results_path = get_json_path('data/results', f'{teacher.username}.json')
    results_data = read_json(results_path)

    # Check if student already took the quiz
    for result in results_data:
        if result.get("student_id") == student.id:
            return jsonify(success=False, message="You have already completed this quiz. You cannot retake it.")

    # Updated path for generated exams
    quiz_path = os.path.join('data', 'exams', 'generated', f'quiz_{teacher.username}.json')
    if not os.path.exists(quiz_path):
        return jsonify(success=False, message="Quiz not found.")

    with open(quiz_path, 'r', encoding='utf-8') as f:
        quiz_questions = json.load(f)

    answers = []
    for i, q in enumerate(quiz_questions):
        user_answer = request.form.get(f'q{i}')
        answers.append(user_answer)

    categories = {
        'Mathematics': 0,
        'Physics': 0,
        'Chemistry': 0,
        'Biology': 0,
        'Computer Science': 0
    }
    totals = {
        'Mathematics': 0,
        'Physics': 0,
        'Chemistry': 0,
        'Biology': 0,
        'Computer Science': 0
    }
    total_correct = 0

    for i, q in enumerate(quiz_questions):
        cat = q.get('category', 'N/A')
        answer = q.get('answer')
        if cat in categories:
            totals[cat] += 1
            if answers[i] == answer:
                categories[cat] += 1
                total_correct += 1

    result_data = {
        "id": student.id,
        "student_id": student.id,
        "name": student.name,
        "group": student.group,
        "mathematics": f"{categories['Mathematics']}/{totals['Mathematics']}",
        "physics": f"{categories['Physics']}/{totals['Physics']}",
        "chemistry": f"{categories['Chemistry']}/{totals['Chemistry']}",
        "biology": f"{categories['Biology']}/{totals['Biology']}",
        "computer_science": f"{categories['Computer Science']}/{totals['Computer Science']}",
        "total": f"{total_correct}/{len(quiz_questions)}"
    }

    results_data.append(result_data)
    write_json(results_path, results_data)

    new_result = Result(
        student_id=student.id,
        name=student.name,
        group=student.group,
        mathematics=result_data["mathematics"],
        physics=result_data["physics"],
        chemistry=result_data["chemistry"],
        biology=result_data["biology"],
        computer_science=result_data["computer_science"],
        total=result_data["total"]
    )
    db.session.add(new_result)
    db.session.commit()

    summary = f"""
    <b>Results Summary:</b><br>
    Mathematics: {result_data['mathematics']}<br>
    Physics: {result_data['physics']}<br>
    Chemistry: {result_data['chemistry']}<br>
    Biology: {result_data['biology']}<br>
    Computer Science: {result_data['computer_science']}<br>
    <b>Total: {result_data['total']}</b>
    """

    return jsonify(success=True, message="Quiz submitted successfully! 🎉", summary=summary)

@app.route('/download_results_csv')
def download_results_csv():
    if 'teacher_id' not in session:
        return redirect(url_for('login'))
    teacher = get_teacher()
    # Get all results for students of this teacher
    results_list = Result.query.join(Student, Result.student_id == Student.id)\
        .filter(Student.teacher_id == teacher.id).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Group', 'Mathematics', 'Physics', 'Chemistry', 'Biology', 'Computer Science', 'Total'])
    for result in results_list:
        writer.writerow([
            result.student_id,
            result.name,
            result.group,
            result.mathematics,
            result.physics,
            result.chemistry,
            result.biology,
            result.computer_science,
            result.total
        ])
    output.seek(0)
    filename = f"results_{teacher.username}.csv"
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@app.route('/edit_student', methods=['POST'])
def edit_student():
    if 'teacher_id' not in session:
        return jsonify(success=False, message="Not authorized")
    data = request.get_json()
    student_id = int(data.get('id'))
    new_name = data.get('name', '').strip()
    new_group = data.get('group', '').strip()

    # Validation
    if not new_name:
        return jsonify(success=False, message="Name cannot be empty.")
    if not new_group:
        return jsonify(success=False, message="Group cannot be empty.")

    student_db = Student.query.get(student_id)
    if student_db:
        student_db.name = new_name
        student_db.group = new_group
        db.session.commit()
        return jsonify(success=True, name=new_name, group=new_group)
    return jsonify(success=False, message="Student not found")

@app.route('/delete_student', methods=['POST'])
def delete_student():
    if 'teacher_id' not in session:
        return jsonify(success=False, message="Not authorized")
    data = request.get_json()
    student_id = int(data.get('id'))

    # Check if the student has any results
    has_result = Result.query.filter_by(student_id=student_id).first()
    if has_result:
        return jsonify(success=False, message="Cannot delete student who has already taken the exam.")

    student_db = Student.query.get(student_id)
    if student_db:
        db.session.delete(student_db)
        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False, message="Student not found")

@app.route('/reset_student_password', methods=['POST'])
def reset_student_password():
    if 'teacher_id' not in session:
        return jsonify(success=False, message="Not authorized")
    data = request.get_json()
    student_id = int(data.get('id'))

    new_password = generate_random_password(8)
    new_password_hash = generate_password_hash(new_password)

    student_db = Student.query.get(student_id)
    if student_db:
        student_db.password = new_password_hash
        db.session.commit()
        # Return the new password so it can be shown to the teacher
        return jsonify(success=True, password=new_password)
    return jsonify(success=False, message="Student not found")

@app.route('/reset_student_result', methods=['POST'])
def reset_student_result():
    if 'teacher_id' not in session:
        return jsonify(success=False, message="Not authorized")
    data = request.get_json()
    student_id = int(data.get('id'))

    result_db = Result.query.filter_by(student_id=student_id).first()
    if result_db:
        db.session.delete(result_db)
        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False, message="Result not found")

@app.route('/download_passwords_csv')
def download_passwords_csv():
    passwords_to_deliver = session.pop('passwords_to_deliver', None)
    if not passwords_to_deliver:
        flash('No passwords to deliver. Please upload students first.', 'warning')
        return redirect(url_for('teacher'))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Group', 'Username', 'Password'])
    for student in passwords_to_deliver:
        writer.writerow([
            student["ID"],
            student["Name"],
            student["Group"],
            student["Username"],
            student["Password"]
        ])
    output.seek(0)
    filename = "students_passwords.csv"
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)