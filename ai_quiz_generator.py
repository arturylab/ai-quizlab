import requests
import json
import random
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AIQuizGenerator:
    def __init__(self):
        """Initialize the AI quiz generator."""
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        self.api_key = os.getenv('API_KEY')
        self.data_path = "data/exams/precreated"
    
    def generate_questions_openrouter(self, subject, level, num_questions):
        """Generate questions using OpenRouter API with fallback to precreated questions."""
        if not self.api_key:
            return self._load_fallback_questions(subject, level, num_questions)
        
        time.sleep(2)
        
        try:
            prompt = f"""Generate {num_questions} {subject} question for {level} students.

Return only JSON array format:
[{{"question":"Your question here?","options":["Option A","Option B","Option C","Option D"],"answer":"Correct option"}}]

Subject: {subject}
Level: {level}"""
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "microsoft/phi-4-reasoning-plus:free",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
                "max_tokens": 600
            }
            
            response = requests.post(self.openrouter_url, headers=headers, json=payload, timeout=45)
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                questions = self._parse_response(content, subject, level, num_questions)
                
                if len(questions) >= num_questions:
                    final_questions = questions[:num_questions]
                    for i, question in enumerate(final_questions):
                        question['id'] = f"AI-{subject[:4].upper()}-{i+1:03d}"
                    return final_questions
                    
            elif response.status_code == 429:
                print("Rate limit exceeded")
                
        except Exception:
            pass
        
        # Fallback to precreated questions
        return self._load_fallback_questions(subject, level, num_questions)

    def _parse_response(self, response_text, subject, level, expected_count):
        """Simple response parsing."""
        questions = []
        
        # Clean response
        response_text = response_text.strip()
        
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        # Find JSON array
        start = response_text.find('[')
        end = response_text.rfind(']') + 1
        
        if start >= 0 and end > start:
            try:
                json_text = response_text[start:end]
                data = json.loads(json_text)
                
                if isinstance(data, list):
                    for q in data[:expected_count]:
                        if self._is_valid_question(q):
                            questions.append({
                                "question": q["question"],
                                "options": q["options"],
                                "answer": q["answer"],
                                "category": subject,
                                "level": level
                            })
            except:
                pass
        
        return questions

    def _is_valid_question(self, q):
        """Simple validation."""
        try:
            return (isinstance(q, dict) and 
                    "question" in q and 
                    "options" in q and 
                    "answer" in q and
                    isinstance(q["options"], list) and 
                    len(q["options"]) == 4 and
                    q["answer"] in q["options"])
        except:
            return False

    def _load_fallback_questions(self, subject, level, num_needed):
        """Load questions from precreated JSON files."""
        questions = []
        
        subject_map = {
            'Mathematics': 'math',
            'Physics': 'physics', 
            'Chemistry': 'chemistry',
            'Biology': 'biology',
            'Computer Science': 'computerscience'
        }
        
        level_map = {
            'Elementary': 'elementary',
            'Middle School': 'middle_school',
            'High School': 'high_school'
        }
        
        file_key = subject_map.get(subject, subject.lower())
        level_folder = level_map.get(level, level.lower().replace(' ', '_'))
        file_path = os.path.join(self.data_path, level_folder, f"{file_key}.json")
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    all_questions = json.load(f)
                    
                    if all_questions:
                        selected = random.sample(all_questions, min(num_needed, len(all_questions)))
                        
                        for q in selected:
                            questions.append({
                                "question": q.get("question", ""),
                                "options": q.get("options", []),
                                "answer": q.get("answer", ""),
                                "category": subject,
                                "level": level
                            })
        except:
            pass
        
        return questions[:num_needed]