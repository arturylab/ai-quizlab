# Installation Guide 🛠️

Complete setup instructions for AI QuizLab on macOS, Linux, and Windows.

## System Requirements

### Minimum Requirements
- **OS**: macOS 10.15+, Ubuntu 18.04+, Windows 10+
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **Network**: Internet connection for AI features

### Required Software
- **PostgreSQL**: 12 or higher
- **Ollama**: Latest version for AI generation
- **Git**: For version control

## Step-by-Step Installation

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/ai-quizlab.git
cd ai-quizlab
```

### 2. Python Environment Setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup

#### Install PostgreSQL
**macOS (Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
Download from [PostgreSQL Official Site](https://www.postgresql.org/download/windows/)

#### Create Database
```bash
# Create database
createdb ai_quizlab

# Verify connection
psql ai_quizlab -c "SELECT version();"
```

### 4. Environment Configuration

Create `.env` file in project root:
```env
SECRET_KEY=your_super_secret_key_here_change_in_production
DATABASE_URL=postgresql://username:password@localhost:5432/ai_quizlab
```

**Generate secure secret key:**
```python
import secrets
print(secrets.token_hex(32))
```

### 5. Ollama Installation

#### Install Ollama
**macOS:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download from [Ollama Official Site](https://ollama.ai)

#### Start Ollama Service
```bash
ollama serve
```

### 6. Import Question Bank (Recommended)

Import the pre-created question bank with 350 questions across all subjects and difficulty levels:

```bash
# Import question bank from CSV file
python migrate_questions.py
```

This will import:
- **Mathematics**: 75 questions across all difficulty levels
- **Physics**: 75 questions across all difficulty levels  
- **Chemistry**: 75 questions across all difficulty levels
- **Biology**: 75 questions across all difficulty levels
- **Computer Science**: 75 questions across all difficulty levels

**Total: 350 questions** ready for quiz creation!

**Note**: The questions are imported from `migrations/question_bank.csv` which contains the complete question database exported from the original system.

### 7. Install and start Ollama

```bash
# Install Ollama (visit https://ollama.ai for instructions)

# Pull the required model (phi3:mini - lightweight and efficient)
ollama pull phi3:mini

# Start Ollama service
ollama serve  # Start Ollama service on localhost:11434
```

### 8. Access the application

Navigate to `http://localhost:5001`

## Verification

### Check Installation
1. **Database**: `python config.py` should show ✅ connection successful
2. **Question Bank**: Should show "✅ Successfully imported 350 questions"
3. **Ollama**: Visit `http://localhost:11434` - should respond
4. **Application**: Visit `http://localhost:5001` - should show login page

### Create First Teacher Account
1. Navigate to `http://localhost:5001`
2. Click "Register here" 
3. Fill teacher registration form
4. Login with new credentials
5. **Test Quiz Creation**: Try creating a quiz using question bank sources

### Test Both Question Sources
- **Question Bank Test**: Create quiz with only "Question Bank" sources enabled
- **AI Generation Test**: Create quiz with only "AI Generation" checkboxes enabled (requires Ollama)
- **Hybrid Test**: Create quiz with both sources enabled for comparison