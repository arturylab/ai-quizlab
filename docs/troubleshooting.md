# Troubleshooting Guide 🔧

Common issues and solutions for AI QuizLab.

## Installation Issues

### Database Connection Problems

#### PostgreSQL Not Running
```
Error: Database connection failed
Solution:
# Check if PostgreSQL is running
pg_ctl status

# Start PostgreSQL
# macOS (Homebrew):
brew services start postgresql
# Linux:
sudo systemctl start postgresql
# Windows:
net start postgresql-x64-13
```

#### Database Does Not Exist
```
Error: database "ai_quizlab" does not exist
Solution:
createdb ai_quizlab
```

#### Wrong Database URL
```
Error: could not connect to server
Solution: Check .env file DATABASE_URL format:
postgresql://username:password@localhost:5432/ai_quizlab
```

### Python Environment Issues

#### Missing Dependencies
```
Error: ModuleNotFoundError: No module named 'flask'
Solution:
# Activate virtual environment first
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

#### Python Version Conflicts
```
Error: Python 3.8+ required
Solution:
# Check Python version
python --version

# Use specific Python version
python3.8 -m venv venv
```

## AI Integration Issues

### Ollama Connection Problems

#### Ollama Not Running
```
Error: Cannot connect to Ollama
Symptoms: AI generation fails, timeout errors
Solution:
# Start Ollama service
ollama serve

# Verify it's running
curl http://localhost:11434
```

#### Port Conflicts
```
Error: Address already in use
Solution:
# Kill existing Ollama process
pkill ollama

# Start again
ollama serve

# Or use different port
OLLAMA_HOST=0.0.0.0:11435 ollama serve
```

#### Model Not Available
```
Error: model "llama2" not found
Solution:
# Pull required model
ollama pull llama2

# List available models
ollama list
```

### AI Generation Issues

#### Slow Generation
```
Problem: AI questions take too long to generate
Causes: Limited RAM, CPU, or complex requests
Solutions:
1. Reduce question count per category
2. Use simpler models (e.g., smaller Llama variants)
3. Close other applications
4. Increase system RAM
```

#### Poor Question Quality
```
Problem: Generated questions are unclear or incorrect
Solutions:
1. Use different model (mistral vs llama2)
2. Adjust temperature in ai_quiz.py
3. Modify prompts for clarity
4. Use bank questions instead
```

#### Generation Fails Completely
```
Error: AI generation failed for all categories
Solutions:
1. Check Ollama logs: ollama logs
2. Restart Ollama service
3. Use bank questions as fallback
4. Reduce concurrent requests
```

## Application Runtime Issues

### Login Problems

#### Cannot Create Teacher Account
```
Error: Username already exists
Solution: Choose different username or check for typos
```

#### Password Issues
```
Error: Invalid username or password
Solutions:
1. Check caps lock
2. Verify username/password combination
3. Reset password via profile page
```

#### Session Expires Quickly
```
Problem: Logged out frequently
Solution: Check session configuration in config.py
PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
```

### File Upload Issues

#### CSV Upload Fails
```
Error: Invalid file format
Solutions:
1. Verify CSV format:
   exp,name,group
   2001,Alice Walker,A
   
2. Check file encoding (UTF-8)
3. Remove special characters
4. Ensure .csv extension
```

#### Large File Upload
```
Error: File too large
Solution: Check MAX_CONTENT_LENGTH in config.py
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
```

### Quiz Creation Issues

#### No Questions Generated
```
Problem: Quiz creation succeeds but no questions
Causes:
1. Empty question bank
2. AI generation failed
3. No matching criteria

Solutions:
1. Run: python debug_questions.py
2. Check Ollama status
3. Verify category/level combinations
```

#### Mixed Source Problems
```
Problem: Some categories work, others don't
Diagnosis:
- Check which sources failed (AI vs Bank)
- Review quiz creation messages
- Test each category individually
```

## Performance Issues

### Slow Application Response

#### Database Queries
```
Problem: Pages load slowly
Solutions:
1. Add database indexes
2. Optimize queries in models.py
3. Use database connection pooling
4. Check PostgreSQL performance
```

#### Large Student Lists
```
Problem: Student table loads slowly
Solutions:
1. Implement pagination
2. Limit displayed results
3. Use AJAX for updates
4. Optimize JavaScript rendering
```

### Memory Usage

#### High RAM Usage
```
Problem: Application consumes too much memory
Causes: Ollama, large datasets, memory leaks
Solutions:
1. Monitor with: htop or Task Manager
2. Restart Ollama periodically
3. Clear browser cache
4. Optimize database queries
```

## Network & Security Issues

### Port Conflicts

#### Application Port Busy
```
Error: Port 5001 already in use
Solutions:
# Find process using port
lsof -i :5001

# Kill process or use different port
python app.py --port 5002
```

#### Firewall Issues
```
Problem: Cannot access from other devices
Solutions:
1. Configure firewall rules
2. Use 0.0.0.0 instead of localhost
3. Check network configuration
```

### Security Warnings

#### Secret Key Warnings
```
Warning: Using default secret key
Solution: Set proper SECRET_KEY in .env file
SECRET_KEY=your_generated_secret_key_here
```

#### Database Security
```
Problem: Database access warnings
Solutions:
1. Use strong passwords
2. Limit database user permissions
3. Enable SSL connections
4. Regular security updates
```

## Data Issues

### Student Data Problems

#### Duplicate Students
```
Error: Username already exists
Solutions:
1. Check for existing students
2. Use unique identifiers
3. Update instead of create
4. Remove duplicates manually
```

#### Missing Results
```
Problem: Student results not showing
Causes:
1. Quiz not submitted properly
2. Database transaction failed
3. Network interruption

Solutions:
1. Check database logs
2. Allow student to retake
3. Verify quiz completion
```

### Database Corruption

#### Table Errors
```
Error: relation "students" does not exist
Solution:
# Recreate tables
python app.py
# Or manually:
flask db upgrade
```

#### Data Inconsistency
```
Problem: Student count doesn't match results
Solutions:
1. Check foreign key constraints
2. Clean orphaned records
3. Rebuild relationships
4. Database integrity check
```

## Migration Issues

### CSV Import Problems

#### File Not Found
```
Error: CSV file not found: migrations/question_bank.csv
Solution: Ensure the CSV file exists in the migrations folder
Check: ls migrations/question_bank.csv
```

#### Encoding Issues
```
Error: UnicodeDecodeError during CSV reading
Solution: Ensure CSV file is saved with UTF-8 encoding
Fix: Re-export CSV with UTF-8 encoding from pgAdmin
```

#### Malformed CSV
```
Error: Error processing row X: list index out of range
Solution: Check CSV format - should have 10 columns
Verify: Open CSV in text editor and check structure
```

### Question Bank Issues

#### No Questions Available
```
Problem: Quiz creation shows "No questions available"
Causes: Migration failed or question bank empty
Solutions:
1. Run: python migrate_questions.py
2. Check distribution with migration script
3. Verify database tables exist
```

#### Duplicate Questions
```
Problem: Same questions appearing multiple times
Cause: Multiple migration runs without cleanup
Solution: Clear question bank and re-import:
# WARNING: This deletes all questions
DELETE FROM question_bank;
python migrate_questions.py
```

## Debugging Tools

### Log Analysis
```bash
# Application logs
tail -f app.log

# PostgreSQL logs
tail -f /var/log/postgresql/postgresql-13-main.log

# Ollama logs
ollama logs
```

### Database Inspection
```sql
-- Check student count
SELECT COUNT(*) FROM students;

-- Check quiz questions
SELECT category, COUNT(*) FROM quiz_questions GROUP BY category;

-- Check results
SELECT * FROM results ORDER BY id DESC LIMIT 10;
```

### Connection Testing
```python
# Test database
python config.py

# Test AI
python -c "from ai_quiz import QuizGenerator; print(QuizGenerator().check_ollama_connection())"

# Test application
curl http://localhost:5001
```

## Getting Help

### Log Collection
When reporting issues, include:
1. **Error messages**: Complete error text
2. **System info**: OS, Python version, RAM
3. **Steps to reproduce**: Exact sequence
4. **Configuration**: Relevant config settings

### Community Resources
- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Check other docs files
- **Stack Overflow**: General Flask/PostgreSQL questions

### Emergency Recovery
```bash
# Complete reset (CAUTION: Loses all data)
dropdb ai_quizlab
createdb ai_quizlab
python app.py
python debug_questions.py
```

## Prevention Tips

### Regular Maintenance
1. **Database backups**: Weekly exports
2. **System updates**: Keep dependencies current  
3. **Log rotation**: Prevent disk space issues
4. **Performance monitoring**: Track resource usage

### Best Practices
1. **Test changes**: Use development environment
2. **Gradual updates**: One component at a time
3. **Documentation**: Keep track of customizations
4. **Monitoring**: Set up alerts for critical issues

---

Still having issues? Check other documentation files or create a GitHub issue with detailed information.