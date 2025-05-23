from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.security import generate_password_hash
from config import Config
from models import db, Teacher, Student
import csv
import random
import string
import os
import json
import io

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

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
            flash('Login successful!', 'success')
            return redirect(url_for('teacher'))

        # Try student login
        student = Student.query.filter_by(username=username).first()
        if student and student.check_password(password):
            session['student_id'] = student.id
            flash('Login successful!', 'success')
            return redirect(url_for('student'))

        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('teacher_id', None)
    flash('Logged out successfully.', 'info')
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

        existing_user = Teacher.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists.', 'danger')
            return render_template('register.html')

        existing_email = Teacher.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already registered.', 'danger')
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
        flash('Teacher registered successfully! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/teacher')
def teacher():
    if 'teacher_id' not in session:
        return redirect(url_for('login'))
    teacher = Teacher.query.get(session['teacher_id'])
    students_list = []
    json_path = os.path.join('json', f'students_{teacher.username}.json')
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            students_list = json.load(f)
    return render_template('teacher.html', teacher_name=teacher.name, students_list=students_list)

@app.route('/upload', methods=['POST'])
def upload_students():
    if 'teacher_id' not in session:
        flash('You must be logged in as a teacher.', 'danger')
        return redirect(url_for('login'))

    file = request.files.get('file')
    if not file or not file.filename.endswith('.csv'):
        flash('Please upload a valid CSV file.', 'danger')
        return redirect(url_for('teacher'))

    csvfile = file.stream.read().decode('utf-8').splitlines()
    reader = csv.DictReader(csvfile)
    added = 0
    students_json = []

    for row in reader:
        exp = str(row['exp'])
        name = row['name']
        group = row['group']
        username = exp
        password_plain = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        password_hash = generate_password_hash(password_plain)

        if Student.query.filter_by(username=username).first():
            continue

        student = Student(
            name=name,
            group=group,
            username=username,
            password=password_hash,
            teacher_id=session['teacher_id']
        )
        db.session.add(student)
        db.session.flush()  # Get the student.id before commit

        students_json.append({
            "ID": student.id,
            "Name": name,
            "Group": group,
            "Username": username,
            "Password": password_plain
        })
        added += 1

    db.session.commit()

    # Save JSON file
    if not os.path.exists('json'):
        os.makedirs('json')
    teacher = Teacher.query.get(session['teacher_id'])
    json_path = os.path.join('json', f'students_{teacher.username}.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(students_json, f, ensure_ascii=False, indent=4)

    flash(f'{added} students added successfully! Credentials saved in students_{teacher.username}.json', 'success')
    return redirect(url_for('teacher'))

@app.route('/download_students_csv')
def download_students_csv():
    if 'teacher_id' not in session:
        flash('You must be logged in as a teacher.', 'danger')
        return redirect(url_for('login'))
    teacher = Teacher.query.get(session['teacher_id'])
    json_path = os.path.join('json', f'students_{teacher.username}.json')
    if not os.path.exists(json_path):
        flash('No student list found to download.', 'danger')
        return redirect(url_for('teacher'))

    with open(json_path, 'r', encoding='utf-8') as f:
        students_list = json.load(f)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Group', 'Username', 'Password'])
    for student in students_list:
        writer.writerow([
            student.get('ID', ''),
            student.get('Name', ''),
            student.get('Group', ''),
            student.get('Username', ''),
            student.get('Password', '')
        ])
    output.seek(0)
    filename = f"students_list_{teacher.username}.csv"
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@app.route('/student')
def student():
    if 'student_id' not in session:
        return redirect(url_for('login'))
    student = Student.query.get(session['student_id'])
    return render_template('student.html', student_name=student.name)

@app.route('/quiz')
def quiz():
    return render_template('quiz.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)