from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    school = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    students = db.relationship('Student', backref='teacher', lazy=True)
    quizzes = db.relationship('Quiz', backref='teacher', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    group = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    results = db.relationship('Result', backref='student', uselist=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)

class Result(db.Model):
    __tablename__ = 'results'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    group = db.Column(db.String(50), nullable=False)
    mathematics = db.Column(db.String(20), default='0/0')
    physics = db.Column(db.String(20), default='0/0')
    chemistry = db.Column(db.String(20), default='0/0')
    biology = db.Column(db.String(20), default='0/0')
    computer_science = db.Column(db.String(20), default='0/0')
    total = db.Column(db.String(20), default='0/0')

# ✨ NUEVOS MODELOS PARA PREGUNTAS

class QuestionBank(db.Model):
    """Banco de preguntas precreadas (reemplaza archivos JSON en data/exams/precreated)"""
    __tablename__ = 'question_bank'
    
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    option_d = db.Column(db.String(255), nullable=False)
    correct_answer = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # Mathematics, Physics, Chemistry, Biology, Computer Science
    level = db.Column(db.String(50), nullable=False)     # Elementary, Middle School, High School
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convertir a formato compatible con el sistema actual"""
        return {
            'question': self.question,
            'options': [self.option_a, self.option_b, self.option_c, self.option_d],
            'answer': self.correct_answer,
            'category': self.category,
            'level': self.level,
            'id': f'BANK-{self.category[:4].upper()}-{self.id:03d}'
        }

class Quiz(db.Model):
    """Quizzes generados temporalmente (reemplaza archivos JSON en data/exams/generated)"""
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    name = db.Column(db.String(100), default='Generated Quiz')
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    questions = db.relationship('QuizQuestion', backref='quiz', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convertir quiz completo a formato JSON"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'questions': [q.to_dict() for q in self.questions]
        }

class QuizQuestion(db.Model):
    """Preguntas individuales de un quiz generado"""
    __tablename__ = 'quiz_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    option_d = db.Column(db.String(255), nullable=False)
    correct_answer = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    level = db.Column(db.String(50), nullable=False)
    source = db.Column(db.String(20), default='AI')  # 'AI' o 'BANK'
    order_index = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        """Convertir a formato compatible con el sistema actual"""
        return {
            'question': self.question,
            'options': [self.option_a, self.option_b, self.option_c, self.option_d],
            'answer': self.correct_answer,
            'category': self.category,
            'level': self.level,
            'id': f'{self.source}-{self.category[:4].upper()}-{self.id:03d}'
        }