# AI Integration Guide 🤖

Complete guide to Ollama integration and AI question generation in AI QuizLab.

## Overview

AI QuizLab uses **Ollama** to generate dynamic, contextual science questions across multiple subjects and difficulty levels. This guide covers setup, configuration, and troubleshooting of AI features.

## Ollama Setup

### Installation

#### macOS
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

#### Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

#### Windows
Download installer from [ollama.ai](https://ollama.ai)

### Service Management

#### Start Ollama
```bash
ollama serve
```
- Runs on `localhost:11434` by default
- Keep running while using AI features

#### Verify Installation
```bash
curl http://localhost:11434
# Should return Ollama version info
```

## AI Question Generation

### How It Works

1. **Input**: Subject, difficulty level, question count
2. **Processing**: Ollama generates questions using LLM
3. **Format**: CSV with question, options, answer, metadata
4. **Integration**: Questions stored in database as QuizQuestion objects

### Generation Process

#### Teacher Interface
```javascript
// When teacher selects AI generation:
1. Toggle AI checkbox for category
2. Set question count and difficulty  
3. Click "Create Quiz"
4. System generates questions via Ollama
5. Questions integrated with bank questions
```

#### Behind the Scenes
```python
# AI generation workflow:
def create_unified_quiz():
    1. Parse form data (AI vs Bank per category)
    2. Generate AI questions via QuizGenerator
    3. Load bank questions from database
    4. Combine and save to Quiz/QuizQuestion tables
    5. Return success/failure status
```

## Configuration

### Default Settings
```python
# ai_quiz.py configuration
OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "phi3:mini"  # Lightweight and efficient model
REQUEST_TIMEOUT = 60         # API timeout in seconds
```

### Custom Models

#### Available Models
```bash
# List available models
ollama list

# Pull specific model
ollama pull phi3:mini
ollama pull mistral
ollama pull codellama
```

#### Model Selection
Modify `ai_quiz.py` to use different models:
```python
def generate_questions(self, subject, level, num_questions):
    model = "mistral"  # Change here
    # ... rest of method
```

## Question Quality Control

### AI Prompt Engineering

The system uses carefully crafted prompts for quality:

```python
prompt = f"""Generate {num_questions} multiple-choice science questions about {subject} 
at {level} level. Requirements:
- Exactly 4 options (A, B, C, D)
- One correct answer
- Educational and age-appropriate
- Clear, unambiguous questions
- Avoid trick questions
Format as CSV: question,option_a,option_b,option_c,option_d,correct_answer,category,level"""
```

### Quality Metrics
- **Relevance**: Questions match subject and level
- **Clarity**: Unambiguous language
- **Accuracy**: Scientifically correct answers
- **Difficulty**: Appropriate for target level

## Hybrid Question Sources

### Bank + AI Combination
Teachers can mix sources per category:
- Mathematics: 5 questions from Bank
- Physics: 3 questions from AI
- Chemistry: 0 questions (skip)
- Biology: 2 questions from AI
- Computer Science: 4 questions from Bank

### Source Indicators
Questions are tagged with source:
```python
# Database fields
source = 'AI' or 'BANK'
category = 'Mathematics', 'Physics', etc.
level = 'Elementary', 'Middle School', 'High School'
```

## Performance Considerations

### Generation Speed
- **Bank Questions**: Instant retrieval
- **AI Questions**: 5-30 seconds per category
- **Total Time**: Depends on AI question count

### Resource Usage
- **Memory**: Ollama requires 4-8GB RAM
- **CPU**: Intensive during generation
- **Network**: Local processing (no external API)

### Optimization Tips
1. **Pre-generate**: Create questions during low-usage periods
2. **Batch Processing**: Generate multiple categories together
3. **Caching**: Store frequently used questions
4. **Fallback**: Always have bank questions available

## Error Handling

### Common Issues

#### Ollama Not Running
```
Error: Cannot connect to Ollama
Solution: Start ollama service
Command: ollama serve
```

#### Model Not Available
```
Error: Model 'phi3:mini' not found
Solution: Pull required model
Command: ollama pull phi3:mini
```

#### Generation Timeout
```
Error: AI generation timeout
Solution: Reduce question count or check system resources
```

### Fallback Mechanisms
1. **AI Failure**: System falls back to bank questions
2. **Partial Success**: Uses generated questions + fills with bank
3. **Complete Failure**: Shows error, suggests bank-only quiz

## Advanced Configuration

### Custom Prompts
Modify prompts in `ai_quiz.py`:
```python
def create_subject_prompt(self, subject, level, num_questions):
    # Customize prompts per subject
    if subject == "Mathematics":
        return f"Generate {num_questions} math word problems..."
    elif subject == "Physics":
        return f"Generate {num_questions} physics concepts..."
    # ... etc
```

### Model Parameters

Currently, the application uses Ollama's default parameters. However, these can be modified in `ai_quiz.py` by updating the `call_api` method:

```python
# Current implementation (uses Ollama defaults)
payload = {
    "model": self.model,
    "prompt": prompt,
    "stream": False
}

# Modified implementation with custom parameters
payload = {
    "model": self.model,
    "prompt": prompt,
    "stream": False,
    "options": {
        "temperature": 0.7,    # Adjust creativity vs consistency (0.1-1.0)
        "num_predict": 2000,   # Maximum response length
        "top_k": 40,          # Limit vocabulary for more focused responses
        "top_p": 0.9          # Nucleus sampling for coherent responses
    }
}
```

**Parameter Guidelines:**
- **temperature**: `0.3` (more consistent) to `0.9` (more creative)
- **num_predict**: `1500` (shorter responses) to `3000` (longer responses)
- **top_k**: `10-100` (lower = more focused vocabulary)
- **top_p**: `0.8-0.95` (higher = more diverse responses)

**Note**: These parameters require code modification in the `call_api` method of `ai_quiz.py`.

### Integration Testing
```bash
# Test AI connection
python -c "from ai_quiz import QuizGenerator; qg = QuizGenerator(); print(qg.check_ollama_connection())"

# Test question generation
python -c "from ai_quiz import QuizGenerator; qg = QuizGenerator(); print(qg.generate_questions('Mathematics', 'Elementary', 2))"
```

## Monitoring & Debugging

### Log Files
```python
# Enable detailed logging in ai_quiz.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Metrics
- Track generation time per question
- Monitor success/failure rates
- Log model performance

### Health Checks
```python
def health_check():
    return {
        'ollama_status': check_ollama_connection(),
        'models_available': get_available_models(),
        'generation_test': test_generation()
    }
```

## Next Steps

🛠️ Technical implementation details → [API Reference](api-reference.md)
👥 User workflows with AI → [User Guide](user-guide.md)
❓ AI-specific problems → [Troubleshooting](troubleshooting.md)