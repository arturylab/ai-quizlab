# AI QuizLab 🤖

An intelligent quiz management system that combines AI-powered question generation with traditional template-based quizzes. Built with Flask, this application allows teachers to create customized exams using OpenRouter's AI models or pre-curated question banks.

## ✨ Features

### 🧠 AI-Powered Question Generation
- **Intelligent Quiz Creation**: Generate fresh, unique questions using OpenRouter's advanced AI models
- **Hybrid Approach**: Seamlessly fallback to pre-created questions when AI is unavailable
- **Real-time Progress Tracking**: Visual progress bar showing generation status
- **Smart Categorization**: AI generates questions tailored to specific academic levels (Elementary, Middle School, High School)

### 👩‍🏫 Teacher Dashboard
- **Student Management**: Upload CSV files, edit student information, reset passwords
- **Quiz Creation**: Choose between AI generation or template-based questions
- **Progress Monitoring**: Real-time tracking during quiz generation
- **Results Analytics**: Download comprehensive CSV reports
- **Flexible Quiz Settings**: Select subjects, difficulty levels, and question counts

### 👨‍🎓 Student Interface
- **Interactive Quizzes**: Clean, responsive quiz interface
- **Instant Results**: Immediate feedback upon submission
- **Score Breakdown**: Detailed performance analysis by subject
- **One-time Completion**: Prevents retaking unless authorized by teacher

### 📊 Advanced Analytics
- **Multi-subject Scoring**: Mathematics, Physics, Chemistry, Biology, Computer Science
- **CSV Export**: Download student lists and detailed results
- **Performance Tracking**: Monitor individual and class progress
- **Retry Management**: Teachers can reset student attempts

## 🛠️ Technology Stack

- **Backend**: Flask, SQLAlchemy, Flask-Migrate
- **AI Integration**: OpenRouter API with multiple AI models
- **Database**: PostgreSQL (production) / SQLite (development)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **File Processing**: CSV import/export functionality

## 📋 Prerequisites

- Python 3.8+
- OpenRouter API key (for AI question generation)
- PostgreSQL (for production) or SQLite (for development)

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/AI-QuizLab.git
cd AI-QuizLab
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Get OpenRouter API Key (Optional - for AI features)
1. Visit [OpenRouter.ai](https://openrouter.ai)
2. Create an account and generate an API key
3. Add credits to your account for AI model access

### 5. Set Up Environment Variables
Create a `.env` file in the root directory:
```env
SECRET_KEY=your-secret-key-here
API_KEY=your-openrouter-api-key-here
DATABASE_URL=sqlite:///quiz_app.db  # For development
# DATABASE_URL=postgresql://user:password@localhost/dbname  # For production
```

### 6. Initialize Database
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 7. Run the Application
```bash
python app.py
```

The application will be available at `http://localhost:5001`

## 📝 Usage

### Teacher Workflow

1. **Registration/Login**: Create teacher account or log in
2. **Student Management**: 
   - Upload CSV file with student data (format: `exp,name,group`)
   - Automatically generate secure passwords
   - Download student credentials
3. **Quiz Creation**:
   - Enable AI generation for fresh questions
   - Select subjects and difficulty levels
   - Monitor real-time generation progress
   - Preview generated quiz
4. **Results Management**:
   - View student performance
   - Download detailed analytics
   - Allow quiz retakes when needed

### Student Workflow

1. **Login**: Use credentials provided by teacher
2. **Take Quiz**: Complete assigned quiz questions
3. **View Results**: See immediate feedback and scores
4. **One-time Completion**: Cannot retake unless teacher authorizes

## 🧬 AI Question Generation

### How It Works
- **Primary**: Uses OpenRouter API with advanced AI models for intelligent question generation
- **Fallback**: Automatically uses pre-created question bank if AI unavailable or rate limited
- **Quality Assurance**: AI-generated questions are validated for format and content
- **Performance**: Optimized prompts for fast, accurate generation

### Supported AI Models
- **Microsoft Phi-4 Reasoning Plus** (Free tier with daily limits)
- **GPT-3.5 Turbo** (Paid, reliable and fast)
- **Claude-3 Haiku** (Paid, high quality)
- **Automatic Fallback**: Switches to pre-created questions when needed

### Supported Subjects & Levels
- **Subjects**: Mathematics, Physics, Chemistry, Biology, Computer Science
- **Levels**: Elementary, Middle School, High School
- **Question Bank**: 25+ pre-created questions per subject/level combination

## 📁 Project Structure

```
AI-QuizLab/
├── app.py                 # Main Flask application
├── ai_quiz_generator.py   # OpenRouter AI integration
├── models.py              # Database models
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (API keys)
├── static/
│   ├── script.js         # Enhanced frontend logic
│   └── styles.css        # Application styling
├── templates/            # Jinja2 templates
│   ├── teacher.html      # Enhanced teacher dashboard
│   ├── quiz.html         # Student quiz interface
│   └── ...
├── data/
│   ├── exams/
│   │   ├── generated/    # AI & teacher-generated quizzes
│   │   └── precreated/   # Template question bank
│   │       ├── elementary/
│   │       ├── middle_school/
│   │       └── high_school/
│   └── results/          # Quiz results storage
└── migrations/           # Database migration files
```

## 🔧 Configuration

### AI Settings
- **Model**: Microsoft Phi-4 Reasoning Plus (free tier) or paid models
- **Fallback**: Automatic fallback to pre-created questions
- **Rate Limiting**: Handles API limits gracefully
- **Quality Control**: Format validation and content filtering

### Database Configuration
- **Development**: SQLite (default)
- **Production**: PostgreSQL recommended
- **Migrations**: Flask-Migrate for schema management

## 💰 AI Model Costs

### Free Tier
- **Phi-4 Reasoning Plus**: 10 requests per day (free)
- **Rate Limits**: Automatic fallback when exceeded

### Paid Models (Optional)
- **GPT-3.5 Turbo**: ~$0.002 per quiz generation
- **Claude-3 Haiku**: ~$0.003 per quiz generation
- **Higher Limits**: No daily restrictions

## 🚀 Advanced Features

### Real-time Progress Tracking
- Backend progress reporting during AI generation
- Frontend progress bar with category-specific updates
- Error handling and automatic fallback

### Hybrid Question Generation
- Combines AI-generated and pre-created questions
- Intelligent mixing for optimal quiz variety
- Quality assurance for all question types

### Enhanced Student Management
- Bulk CSV upload with error reporting
- Password reset functionality
- Performance analytics and reporting

### Rate Limit Management
- Graceful handling of API rate limits
- Automatic fallback to pre-created questions
- Smart retry logic with delays

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, feature requests, or bug reports, please open an issue on GitHub.

## 🙏 Acknowledgments

- **OpenRouter** for providing access to multiple AI models
- **Microsoft** for the Phi-4 model
- **Anthropic** for Claude models
- **OpenAI** for GPT models
- **Flask** community for the excellent web framework
- Contributors and testers who helped improve the application

---

**AI QuizLab** - Revolutionizing education through intelligent quiz generation 🚀