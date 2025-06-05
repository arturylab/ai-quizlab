# AI QuizLab 🤖

AI QuizLab is an educational web application that combines pre-built question banks with AI-powered question generation using Ollama. The platform helps teachers create dynamic science quizzes and manage student assessments across multiple subjects.

---

## ✨ Features

- 🔐 **Teacher and Student Authentication:** Secure login system with session management.
- 🧑‍🏫 **Teacher Dashboard:** 
  - 📤 Upload student lists via CSV with automatic credential generation.
  - 🤖 **AI Quiz Generation:** Create questions using Ollama AI models.
  - 📚 **Question Bank:** Use pre-built questions from database.
  - 🔄 **Hybrid Quizzes:** Mix AI-generated and bank questions.
  - 📊 View student performance and quiz statistics.
  - ⚙️ Edit profile and manage student accounts.
- 👨‍🎓 **Student Dashboard:** 
  - 🧪 Take science quizzes across multiple subjects.
  - 📈 Track scores and performance by category.
  - 🎯 Subject-specific assessments (Math, Physics, Chemistry, Biology, CS).
- 📂 **CSV Data Management:** Import/export student data and results.
- 🔒 **Security:** Password hashing, session timeouts, and secure credential handling.

---

## 🛠️ Technology Stack

- 🐍 **Backend:** Python 3.8+ with Flask
- 🗄️ **Database:** PostgreSQL with SQLAlchemy ORM
- 🤖 **AI:** Ollama for question generation
- 🖥️ **Frontend:** HTML5, CSS3, JavaScript
- 📦 **Package Management:** pip and requirements.txt

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- **Ollama** installed and running on `localhost:11434`
- Git

### Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/ai-quizlab.git
    cd ai-quizlab
    ```

2. **Create virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # macOS/Linux
    # or venv\Scripts\activate  # Windows
    ```

3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Set up environment variables:**
    ```env
    SECRET_KEY=your_secret_key_here
    DATABASE_URL=postgresql://username:password@localhost:5432/ai_quizlab
    ```

5. **Set up database:**
    ```bash
    createdb ai_quizlab
    python3 app.py  # Creates tables automatically
    ```

6. **Install and start Ollama:**
    ```bash
    # Install Ollama (visit https://ollama.ai for instructions)
    ollama serve  # Start Ollama service
    ```

7. **Access the application:**
   Navigate to `http://localhost:5001`

---

## 🤖 AI Features

### Ollama Integration
- **Automatic question generation** for any subject and difficulty level
- **Fallback system** to question bank if AI is unavailable
- **Mixed source quizzes** combining AI and pre-built questions
- **Real-time generation** with progress feedback

### Question Sources
- 🤖 **AI Generated:** Dynamic questions created by Ollama
- 📚 **Question Bank:** Pre-built questions stored in database
- 🔄 **Hybrid:** Combination of both sources in single quiz

---

## 📝 Usage Guide

### For Teachers 🧑‍🏫

1. **Create Quizzes:**
   - Choose subjects (Math, Physics, Chemistry, Biology, Computer Science)
   - Select difficulty levels (Elementary, Middle School, High School)
   - Toggle between AI generation and question bank per category
   - Generate mixed-source quizzes

2. **Student Management:**
   - Upload CSV files with student data
   - Download generated credentials
   - Reset passwords and manage accounts

### For Students 👨‍🎓

1. **Take Quizzes:**
   - Login with provided credentials
   - Complete science assessments
   - View scores by subject category

---

## 📁 Project Structure

```
ai-quizlab/
├── app.py                  # Main Flask application
├── config.py              # Configuration settings
├── models.py              # Database models
├── utils.py               # Utility functions
├── quiz_utils.py          # Quiz management utilities
├── ai_quiz.py             # Ollama AI integration
├── debug_questions.py     # Sample data seeder
├── requirements.txt       # Dependencies
├── templates/             # HTML templates
├── static/               # CSS, JS, assets
└── docs/                 # Documentation (coming soon)
```

---

## 🔧 Configuration

### CSV Upload Format
```csv
exp,name,group
2001,Alice Walker,A
2002,Brian Lee,A
```

### Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Flask secret key | Yes |
| `DATABASE_URL` | PostgreSQL connection | Yes |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 🐛 Troubleshooting

**Ollama Connection Issues:**
- Ensure Ollama is running on `localhost:11434`
- Check if required models are installed
- Fallback to question bank if AI unavailable

**Database Issues:**
- Verify PostgreSQL is running
- Check DATABASE_URL configuration
- Run `python debug_questions.py` to populate sample data

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**AI QuizLab** – Intelligent science education powered by AI! 🚀🔬🤖