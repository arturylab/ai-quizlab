from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Teacher(db.Model):
    """Teacher model for storing instructor information and authentication."""
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    school = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    
    # Relationships
    students = db.relationship('Student', backref='teacher', lazy=True)
    quizzes = db.relationship('Quiz', backref='teacher', lazy=True)

    def set_password(self, password):
        """Hash and set the teacher's password."""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify the teacher's password."""
        return check_password_hash(self.password, password)

class Student(db.Model):
    """Student model for storing student information and authentication."""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    group = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    
    # Relationships
    results = db.relationship('Result', backref='student', uselist=False)

    def set_password(self, password):
        """Hash and set the student's password."""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify the student's password."""
        return check_password_hash(self.password, password)

class Result(db.Model):
    """Result model for storing student exam scores by category."""
    __tablename__ = 'results'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    group = db.Column(db.String(50), nullable=False)
    
    # Score fields for each subject category
    mathematics = db.Column(db.String(20), default='0/0')
    physics = db.Column(db.String(20), default='0/0')
    chemistry = db.Column(db.String(20), default='0/0')
    biology = db.Column(db.String(20), default='0/0')
    computer_science = db.Column(db.String(20), default='0/0')
    total = db.Column(db.String(20), default='0/0')

class QuestionBank(db.Model):
    """Pre-created question bank (replaces JSON files in data/exams/precreated)."""
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
        """Convert to format compatible with current system."""
        return {
            'question': self.question,
            'options': [self.option_a, self.option_b, self.option_c, self.option_d],
            'answer': self.correct_answer,
            'category': self.category,
            'level': self.level,
            'id': f'BANK-{self.category[:4].upper()}-{self.id:03d}'
        }

class Quiz(db.Model):
    """Temporarily generated quizzes (replaces JSON files in data/exams/generated)."""
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    name = db.Column(db.String(100), default='Generated Quiz')
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('QuizQuestion', backref='quiz', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert complete quiz to JSON format."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'questions': [q.to_dict() for q in self.questions]
        }

class QuizQuestion(db.Model):
    """Individual questions within a generated quiz."""
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
    source = db.Column(db.String(20), default='AI')  # 'AI' or 'BANK'
    order_index = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        """Convert to format compatible with current system."""
        return {
            'question': self.question,
            'options': [self.option_a, self.option_b, self.option_c, self.option_d],
            'answer': self.correct_answer,
            'category': self.category,
            'level': self.level,
            'id': f'{self.source}-{self.category[:4].upper()}-{self.id:03d}'
        }