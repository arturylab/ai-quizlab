# AI QuizLab 🤖

AI QuizLab is an educational web application designed to help students and teachers manage and participate in science quizzes. The platform supports multiple science subjects, user management for teachers and students, and CSV-based student list uploads.

---

## ✨ Features

- 🔐 **Teacher and Student Login:** Secure authentication for both roles with session timeouts for added security.
- 🧑‍🏫 **Teacher Dashboard:** 
  - 📤 Upload student lists via CSV files.
  - 📥 Download student credentials as CSV.
  - 📝 Create and manage quizzes by subject and level, with random question selection for each exam.
  - 👁️ View student lists generated from uploaded CSVs.
  - ⚙️ Edit your profile (name, school, and password) from a dedicated profile page.
- 👨‍🎓 **Student Dashboard:** 
  - 🧪 Participate in science quizzes.
  - ⏰ Session time limits for secure access.
  - 📊 Track quiz progress and results.
- 📂 **CSV Integration:** Easily import and export student data.
- 🔒 **Password Security:** All passwords are securely hashed.
- 🗂️ **JSON Storage:** Student lists are stored per teacher in the `/json` folder for easy access and download.
- 💬 **User Feedback:** Flash messages provide clear feedback for login, registration, profile updates, and errors.

---

## 🛠️ Technologies Used

- 🐍 Python 3
- ⚗️ Flask
- 🗄️ Flask-SQLAlchemy
- 🐘 PostgreSQL
- 🖥️ HTML5, CSS3
- 💻 JavaScript (for frontend enhancements and profile editing)

---

## 🚀 Getting Started

### Prerequisites

- Python 3.x
- PostgreSQL
- pip (Python package manager)

### Installation

1. **Clone the repository:**
    ```sh
    git clone https://github.com/yourusername/ai-quizlab.git
    cd ai-quizlab
    ```

2. **Create and activate a virtual environment:**
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

4. **Create a `.env` file in the project root:**
    ```
    SECRET_KEY=your_secret_key_here
    DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/ai-quizlab
    ```

5. **Initialize the database:**
    ```sh
    python3 app.py
    ```
    The tables will be created automatically on first run.

---

## 📝 Usage

- 🧑‍🏫 **Teachers:** Register via the `/register` page, then log in to upload student lists, manage quizzes, and edit your profile. Uploaded student lists are stored as JSON files in the `/json` folder and can be downloaded as CSV.
- 👨‍🎓 **Students:** Log in with credentials provided by their teacher to access quizzes. Session timeouts ensure secure access.
- ⚙️ **Profile Editing:** Teachers can update their name, school, and password from the profile page.
- 📝 **Randomized Exams:** Each quiz is generated with a random selection of questions per subject and level.

---

## 📁 File Structure

- `app.py` - Main Flask application.
- `models.py` - Database models.
- `config.py` - Configuration settings (uses `.env` for secrets and DB URI).
- `templates/` - HTML templates (Jinja2).
- `static/` - Static files (CSS, JS).
- `json/` - Generated student lists per teacher (e.g., `students_frank.json`).
- `.env` - Environment variables (not tracked by git).
- `.gitignore` - Ignores `venv/`, `__pycache__/`, `.env`, `.json`, `.csv`, and credentials files.
- `README.md` - Project documentation.

---

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a pull request.  
Feel free to open issues for suggestions or bugs.

---

## 📄 License

This project is licensed under the MIT License.

---

**AI QuizLab** – Making science learning interactive and fun! 🚀