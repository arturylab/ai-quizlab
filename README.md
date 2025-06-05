# AI QuizLab 🤖

AI QuizLab is an educational web application designed to help students and teachers manage and participate in science quizzes. The platform supports multiple science subjects, user management for teachers and students, and CSV-based student list uploads.

---

## ✨ Features

- 🔐 **Teacher and Student Authentication:** Secure login system for both roles with session timeouts for enhanced security.
- 🧑‍🏫 **Teacher Dashboard:** 
  - 📤 Upload student lists via CSV files with automatic credential generation.
  - 📥 Download student credentials as CSV (passwords available only after upload or reset).
  - 📝 Create and manage quizzes by subject and difficulty level.
  - 🎲 Random question selection for each exam session.
  - 👁️ View comprehensive student lists and performance statistics.
  - ⚙️ Edit profile information (name, school, password) from dedicated profile page.
  - 🔄 Reset student passwords when needed.
- 👨‍🎓 **Student Dashboard:** 
  - 🧪 Access science quizzes across multiple subjects.
  - ⏰ Timed quiz sessions with automatic logout for security.
  - 📊 Track quiz progress, scores, and performance history.
  - 🎯 Subject-specific quiz categories and difficulty levels.
- 📂 **CSV Data Management:** Seamless import and export of student data.
- 🔒 **Advanced Security:** 
  - Password hashing with industry-standard algorithms.
  - Session management with timeout protection.
  - Secure credential handling (plain passwords shown only once).
- 💬 **User Experience:** Flash messaging system for clear feedback on all operations.
- 🎨 **Responsive Design:** Modern, mobile-friendly interface.

---

## 🛠️ Technology Stack

- 🐍 **Backend:** Python 3.8+
- ⚗️ **Web Framework:** Flask with extensions
- 🗄️ **ORM:** Flask-SQLAlchemy
- 🐘 **Database:** PostgreSQL
- 🖥️ **Frontend:** HTML5, CSS3
- 💻 **Client-side:** JavaScript (ES6+)
- 📦 **Package Management:** pip
- 🔧 **Environment Management:** python-dotenv

---

## 🚀 Getting Started

### Prerequisites

Make sure you have the following installed:
- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)
- Git

### Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/ai-quizlab.git
    cd ai-quizlab
    ```

2. **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On macOS/Linux
    # or
    venv\Scripts\activate     # On Windows
    ```

3. **Install required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Set up environment variables:**
   Create a `.env` file in the project root directory:
    ```env
    SECRET_KEY=your_super_secret_key_here_change_this_in_production
    DATABASE_URL=postgresql://username:password@localhost:5432/ai_quizlab
    ```

5. **Set up the database:**
    ```bash
    # Create the database in PostgreSQL first
    createdb ai_quizlab
    
    # Then run the application to auto-create tables
    python3 app.py
    ```

6. **Access the application:**
   Open your browser and navigate to `http://localhost:5001`

---

## 📝 Usage Guide

### For Teachers 🧑‍🏫

1. **Registration & Login:**
   - Navigate to `/register` to create a teacher account
   - Login at `/login` with your credentials

2. **Student Management:**
   - Upload CSV files with student information (Name, Email format)
   - Download generated credentials immediately after upload
   - View all students in your database
   - Reset student passwords when necessary

3. **Quiz Management:**
   - Create quizzes by selecting subjects and difficulty levels
   - Questions are randomly selected for each student session
   - Monitor student performance and statistics

4. **Profile Management:**
   - Update your name, school affiliation, and password
   - Access profile settings from the dashboard

### For Students 👨‍🎓

1. **Login:**
   - Use credentials provided by your teacher
   - Sessions automatically timeout for security

2. **Taking Quizzes:**
   - Select from available science subjects
   - Complete timed quiz sessions
   - View your scores and progress

3. **Performance Tracking:**
   - Review your quiz history
   - Monitor improvement over time

---

## 📁 Project Structure

```
ai-quizlab/
├── app.py              # Main Flask application and routes
├── config.py           # Application configuration
├── models.py           # Database models and schema
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (not in repo)
├── .gitignore          # Git ignore rules
├── README.md           # Project documentation
├── templates/          # Jinja2 HTML templates
│   ├── base.html           # Base template
│   ├── dashboard.html      # Main dashboard
│   ├── login.html          # Login page
│   ├── profile.html        # User profile page
│   ├── quiz.html           # Quiz interface
│   └── register.html       # Registration page
├── static/             # Static assets
│   ├── css/                # Stylesheets
│   ├── js/                 # JavaScript files
│   └── uploads/            # File upload directory
└── migrations/         # Database migration scripts
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key for sessions | Yes | None |
| `DATABASE_URL` | PostgreSQL connection string | Yes | None |

### CSV Upload Format

When uploading student lists, use this CSV format:
```csv
exp,name,group
2001,Alice Walker,A
2002,Brian Lee,A
```

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/amazing-feature`
3. **Commit your changes:** `git commit -m 'Add amazing feature'`
4. **Push to the branch:** `git push origin feature/amazing-feature`
5. **Open a Pull Request`

### Development Guidelines

- Follow PEP 8 style guidelines
- Write descriptive commit messages
- Add tests for new features
- Update documentation as needed

---

## 🐛 Known Issues & Troubleshooting

### Common Issues

1. **Database Connection Error:**
   - Verify PostgreSQL is running
   - Check DATABASE_URL in .env file
   - Ensure database exists

2. **CSV Upload Issues:**
   - Verify CSV format matches expected structure
   - Check file permissions

3. **Session Timeout:**
   - Normal security feature
   - Re-login if session expires


---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---


**AI QuizLab** – Making science education interactive, engaging, and accessible! 🚀🔬