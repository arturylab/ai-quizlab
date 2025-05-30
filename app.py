from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify, flash
from werkzeug.security import generate_password_hash
from datetime import timedelta
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
app.permanent_session_lifetime = timedelta(minutes=30)
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

        existing_user = Teacher.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose another.', 'danger')
            return render_template('register.html')

        existing_email = Teacher.query.filter_by(email=email).first()
        if existing_email:
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
    teacher = Teacher.query.get(session['teacher_id'])
    students_list = []
    json_dir = os.path.join('data', 'teachers')
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)
    json_path = os.path.join(json_dir, f'students_{teacher.username}.json')
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            students_list = json.load(f)

    # Load results for this teacher from JSON, not DB
    results_list = []
    results_dir = os.path.join('data', 'results')
    results_path = os.path.join(results_dir, f'{teacher.username}.json')
    if os.path.exists(results_path):
        with open(results_path, 'r', encoding='utf-8') as f:
            results_list = json.load(f)

    return render_template(
        'teacher.html',
        teacher_name=teacher.name,
        students_list=students_list,
        results_list=results_list
    )

from flask import flash

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'teacher_id' not in session:
        return redirect(url_for('login'))
    teacher = Teacher.query.get(session['teacher_id'])

    if request.method == 'POST':
        name = request.form.get('name', teacher.name)
        school = request.form.get('school', teacher.school)
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Actualiza solo si el nombre cambió
        if name and name != teacher.name:
            teacher.name = name

        # Actualiza solo si la escuela cambió
        if school and school != teacher.school:
            teacher.school = school

        # Actualiza solo si se ingresó un nuevo password
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

    return redirect(url_for('teacher'))

@app.route('/download_students_csv')
def download_students_csv():
    if 'teacher_id' not in session:
        return redirect(url_for('login'))
    teacher = Teacher.query.get(session['teacher_id'])
    json_dir = os.path.join('data', 'teachers')
    json_path = os.path.join(json_dir, f'students_{teacher.username}.json')
    if not os.path.exists(json_path):
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

@app.route('/create_quiz', methods=['POST'])
def create_quiz():
    if 'teacher_id' not in session:
        msg = 'You must be logged in as a teacher.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message=msg)
        return redirect(url_for('login'))

    teacher = Teacher.query.get(session['teacher_id'])
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
            exam_path = os.path.join('data', 'exams_precreated', level_folder, f'{file_key}.json')
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

    generated_dir = os.path.join('data', 'exams_generated')
    if not os.path.exists(generated_dir):
        os.makedirs(generated_dir)
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
    teacher = Teacher.query.get(session['teacher_id'])
    quiz_path = os.path.join('data', 'exams_generated', f'quiz_{teacher.username}.json')
    quiz_questions = []
    if os.path.exists(quiz_path):
        with open(quiz_path, 'r', encoding='utf-8') as f:
            quiz_questions = json.load(f)
    return render_template('exam_teacher.html', teacher_name=teacher.name, quiz_questions=quiz_questions)

@app.route('/student')
def student():
    if 'student_id' not in session:
        return redirect(url_for('login'))
    student = Student.query.get(session['student_id'])
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
    student = Student.query.get(session['student_id'])
    teacher = Teacher.query.get(student.teacher_id) if student else None
    quiz_questions = []
    already_done = False
    student_result = None

    if teacher:
        results_path = os.path.join('data', 'results', f'{teacher.username}.json')
        if os.path.exists(results_path):
            with open(results_path, 'r', encoding='utf-8') as f:
                results_data = json.load(f)
            for result in results_data:
                if result.get("student_id") == student.id:
                    already_done = True
                    student_result = result
                    break

        if not already_done:
            quiz_path = os.path.join('data', 'exams_generated', f'quiz_{teacher.username}.json')
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

    student = Student.query.get(session['student_id'])
    teacher = Teacher.query.get(student.teacher_id) if student else None
    if not teacher:
        return jsonify(success=False, message="Teacher not found.")

    # Ruta del JSON de resultados del maestro
    results_dir = os.path.join('data', 'results')
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    results_filename = f"{teacher.username}.json"
    results_path = os.path.join(results_dir, results_filename)

    # Cargar resultados existentes del maestro
    results_data = []
    if os.path.exists(results_path):
        with open(results_path, 'r', encoding='utf-8') as f:
            results_data = json.load(f)

    # Verificar si el estudiante ya realizó el examen
    for result in results_data:
        if result.get("student_id") == student.id:
            return jsonify(success=False, message="You have already completed this quiz. You cannot retake it.")

    # Cargar el quiz del maestro
    quiz_path = os.path.join('data', 'exams_generated', f'quiz_{teacher.username}.json')
    if not os.path.exists(quiz_path):
        return jsonify(success=False, message="Quiz not found.")

    with open(quiz_path, 'r', encoding='utf-8') as f:
        quiz_questions = json.load(f)

    # Procesar respuestas
    answers = []
    for i, q in enumerate(quiz_questions):
        user_answer = request.form.get(f'q{i}')
        answers.append(user_answer)

    # Calcular resultados por materia
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

    # Formato "aciertos/total"
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

    # Agregar el resultado al JSON del maestro
    results_data.append(result_data)
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, ensure_ascii=False, indent=4)

    # Guardar en la base de datos (tabla Result)
    from models import Result
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

    # Crear resumen para mostrar al estudiante
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
    teacher = Teacher.query.get(session['teacher_id'])
    results_dir = os.path.join('data', 'results')
    results_path = os.path.join(results_dir, f'{teacher.username}.json')
    if not os.path.exists(results_path):
        return redirect(url_for('teacher'))

    with open(results_path, 'r', encoding='utf-8') as f:
        results_list = json.load(f)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Group', 'Mathematics', 'Physics', 'Chemistry', 'Biology', 'Computer Science', 'Total'])
    for result in results_list:
        writer.writerow([
            result.get('id', ''),
            result.get('name', ''),
            result.get('group', ''),
            result.get('mathematics', ''),
            result.get('physics', ''),
            result.get('chemistry', ''),
            result.get('biology', ''),
            result.get('computer_science', ''),
            result.get('total', '')
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
    new_name = data.get('name')
    new_group = data.get('group')

    teacher = Teacher.query.get(session['teacher_id'])
    json_dir = os.path.join('data', 'teachers')
    json_path = os.path.join(json_dir, f'students_{teacher.username}.json')
    if not os.path.exists(json_path):
        return jsonify(success=False, message="Student list not found")

    with open(json_path, 'r', encoding='utf-8') as f:
        students_list = json.load(f)

    updated = False
    for student in students_list:
        if int(student['ID']) == student_id:
            student['Name'] = new_name
            student['Group'] = new_group
            updated = True
            break

    if not updated:
        return jsonify(success=False, message="Student not found")

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(students_list, f, ensure_ascii=False, indent=4)

    # Actualiza también en la base de datos
    student_db = Student.query.get(student_id)
    if student_db:
        student_db.name = new_name
        student_db.group = new_group
        db.session.commit()

    return jsonify(success=True, name=new_name, group=new_group)

@app.route('/delete_student', methods=['POST'])
def delete_student():
    if 'teacher_id' not in session:
        return jsonify(success=False, message="Not authorized")
    data = request.get_json()
    student_id = int(data.get('id'))

    teacher = Teacher.query.get(session['teacher_id'])
    json_dir = os.path.join('data', 'teachers')
    json_path = os.path.join(json_dir, f'students_{teacher.username}.json')
    if not os.path.exists(json_path):
        return jsonify(success=False, message="Student list not found")

    with open(json_path, 'r', encoding='utf-8') as f:
        students_list = json.load(f)

    new_students_list = [s for s in students_list if int(s['ID']) != student_id]
    if len(new_students_list) == len(students_list):
        return jsonify(success=False, message="Student not found")

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(new_students_list, f, ensure_ascii=False, indent=4)

    # Elimina también de la base de datos
    student_db = Student.query.get(student_id)
    if student_db:
        db.session.delete(student_db)
        db.session.commit()

    return jsonify(success=True)

@app.route('/reset_student_password', methods=['POST'])
def reset_student_password():
    if 'teacher_id' not in session:
        return jsonify(success=False, message="Not authorized")
    data = request.get_json()
    student_id = int(data.get('id'))

    # Generar nuevo password aleatorio
    import random, string
    new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    from werkzeug.security import generate_password_hash
    new_password_hash = generate_password_hash(new_password)

    teacher = Teacher.query.get(session['teacher_id'])
    json_dir = os.path.join('data', 'teachers')
    json_path = os.path.join(json_dir, f'students_{teacher.username}.json')
    if not os.path.exists(json_path):
        return jsonify(success=False, message="Student list not found")

    with open(json_path, 'r', encoding='utf-8') as f:
        students_list = json.load(f)

    updated = False
    for student in students_list:
        if int(student['ID']) == student_id:
            student['Password'] = new_password
            updated = True
            break

    if not updated:
        return jsonify(success=False, message="Student not found")

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(students_list, f, ensure_ascii=False, indent=4)

    # Actualiza también en la base de datos
    student_db = Student.query.get(student_id)
    if student_db:
        student_db.password = new_password_hash
        db.session.commit()

    return jsonify(success=True, password=new_password)

@app.route('/reset_student_result', methods=['POST'])
def reset_student_result():
    if 'teacher_id' not in session:
        return jsonify(success=False, message="Not authorized")
    data = request.get_json()
    student_id = int(data.get('id'))

    teacher = Teacher.query.get(session['teacher_id'])
    results_dir = os.path.join('data', 'results')
    results_path = os.path.join(results_dir, f'{teacher.username}.json')
    if not os.path.exists(results_path):
        return jsonify(success=False, message="Results file not found")

    # Elimina del JSON
    with open(results_path, 'r', encoding='utf-8') as f:
        results_list = json.load(f)
    new_results_list = [r for r in results_list if int(r.get('student_id', 0)) != student_id]
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(new_results_list, f, ensure_ascii=False, indent=4)

    # Elimina de la base de datos
    from models import Result
    result_db = Result.query.filter_by(student_id=student_id).first()
    if result_db:
        db.session.delete(result_db)
        db.session.commit()

    return jsonify(success=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)