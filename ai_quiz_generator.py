import requests
import json
import random
import os

class AIQuizGenerator:
    def __init__(self):
        """Initialize the AI quiz generator."""
        self.ollama_url = "http://localhost:11434/api/generate"
        self.available_models = self._check_available_models()
        self.data_path = "data/exams/precreated"
        
    def _check_available_models(self):
        """Check which models are available in Ollama."""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model['name'] for model in models]
        except requests.RequestException:
            print("Warning: Cannot connect to Ollama. Make sure it's running.")
        return []
    
    def generate_questions_ollama(self, subject, level, num_questions, model_name="phi3:mini"):
        """Generate questions using Ollama with fallback to precreated questions."""
        if not self.available_models:
            print("No Ollama models available. Using precreated questions.")
            return self._load_fallback_questions(subject, level, num_questions)
        
        model = model_name if model_name in self.available_models else self.available_models[0]
        print(f"Generating {num_questions} {level} {subject} questions using Ollama ({model})...")
        
        questions = []
        
        # Try to generate with AI first
        try:
            prompt = self._create_fast_prompt(subject, level, num_questions)
            
            response = requests.post(
                self.ollama_url,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.8,
                        "num_predict": min(300 + (num_questions * 80), 800),
                        "repeat_penalty": 1.05,
                        "top_k": 40
                    }
                },
                timeout=45
            )
            
            if response.status_code == 200:
                result = response.json()
                questions = self._parse_fast_response(
                    result.get('response', ''), subject, level, num_questions
                )
                print(f"✓ Generated {len(questions)} AI questions")
                
        except Exception as e:
            print(f"AI generation failed: {e}")
        
        # If AI didn't generate enough questions, fill with precreated ones
        if len(questions) < num_questions:
            missing = num_questions - len(questions)
            print(f"📁 Loading {missing} questions from precreated bank...")
            
            fallback_questions = self._load_fallback_questions(subject, level, missing)
            questions.extend(fallback_questions)
            
            ai_count = len(questions) - len(fallback_questions)
            fallback_count = len(fallback_questions)
            print(f"✅ Final mix: {ai_count} AI + {fallback_count} precreated = {len(questions)} total")
        
        # Assign IDs and trim to exact count
        final_questions = questions[:num_questions]
        for i, question in enumerate(final_questions):
            question['id'] = f"MIX-{subject[:4].upper()}-{i+1:03d}"
        
        print(f"✅ Final result: {len(final_questions)}/{num_questions} questions ready")
        return final_questions

    def _load_fallback_questions(self, subject, level, num_needed):
        """Load questions from precreated JSON files."""
        questions = []
        
        # Map subjects to file names (based on your file structure)
        subject_map = {
            'Mathematics': 'math',
            'Physics': 'physics', 
            'Chemistry': 'chemistry',
            'Biology': 'biology',
            'Computer Science': 'computerscience'
        }
        
        # Map levels to folder names (based on your folder structure)
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
                    
                    # Randomly select questions to avoid repetition
                    if all_questions and len(all_questions) > 0:
                        selected = random.sample(all_questions, min(num_needed, len(all_questions)))
                        
                        for q in selected:
                            questions.append({
                                "question": q.get("question", ""),
                                "options": q.get("options", []),
                                "answer": q.get("answer", ""),
                                "category": subject,
                                "level": level
                            })
                        
                        print(f"✓ Loaded {len(questions)} questions from {level_folder}/{file_key}.json")
                    else:
                        print(f"⚠ No questions found in {file_path}")
            else:
                print(f"⚠ File not found: {file_path}")
                
        except Exception as e:
            print(f"Error loading fallback questions: {e}")
        
        return questions[:num_needed]

    def _create_fast_prompt(self, subject, level, num_questions):
        """Create a simple, fast prompt."""
        return f"""Generate {num_questions} {subject} multiple choice questions for {level} level.

JSON array format:
[{{"question":"What is 2+2?","options":["3","4","5","6"],"answer":"4"}}]

Generate {num_questions} {subject} {level} questions. JSON only."""

    def _parse_fast_response(self, response_text, subject, level, expected_count):
        """Parse response quickly."""
        questions = []
        try:
            # Find JSON array
            text = response_text.strip()
            start = text.find('[')
            end = text.rfind(']') + 1
            
            if start >= 0 and end > start:
                json_text = text[start:end]
                data = json.loads(json_text)
                
                for i, q in enumerate(data[:expected_count]):
                    if isinstance(q, dict) and all(key in q for key in ["question", "options", "answer"]):
                        if isinstance(q["options"], list) and len(q["options"]) == 4:
                            questions.append({
                                "question": q["question"],
                                "options": q["options"],
                                "answer": q["answer"],
                                "category": subject,
                                "level": level
                            })
                            
        except:
            # Try to find individual JSON objects
            import re
            pattern = r'\{"question":"[^"]+","options":\[[^\]]+\],"answer":"[^"]+"\}'
            matches = re.findall(pattern, response_text)
            
            for match in matches[:expected_count]:
                try:
                    q = json.loads(match)
                    questions.append({
                        "question": q["question"],
                        "options": q["options"],
                        "answer": q["answer"],
                        "category": subject,
                        "level": level
                    })
                except:
                    continue
                
        return questions

    def _generate_single_question(self, subject, level, model):
        """Generate one question quickly."""
        try:
            prompt = f"""Generate 1 {subject} question for {level} level.
JSON: {{"question":"...","options":["...","...","...","..."],"answer":"..."}}
{subject} {level} question only."""
            
            response = requests.post(
                self.ollama_url,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.8,
                        "num_predict": 150,
                        "repeat_penalty": 1.1
                    }
                },
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                return self._parse_single_response(result.get('response', ''), subject, level)
                
        except Exception as e:
            print(f"Single question error: {e}")
            
        return None

    def _create_single_question_prompt(self, subject, level):
        """Create prompt for generating a single question."""
        return f"""Generate exactly 1 {subject} multiple choice question for {level} level.

Return only this JSON format:
{{
    "question": "your question here",
    "options": ["option1", "option2", "option3", "option4"],
    "answer": "correct option"
}}

Subject: {subject}
Level: {level}
Return only JSON, no explanations."""

    def _parse_single_response(self, response_text, subject, level):
        """Parse single question response."""
        try:
            response_text = response_text.strip()
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_text = response_text[start:end]
                question_data = json.loads(json_text)
                
                if all(key in question_data for key in ["question", "options", "answer"]):
                    if len(question_data["options"]) == 4:
                        return {
                            "question": question_data["question"],
                            "options": question_data["options"],
                            "answer": question_data["answer"],
                            "category": subject,
                            "level": level
                        }
            
            return None
            
        except:
            return None

    def _create_optimized_prompt(self, subject, level, num_questions):
        """Create an optimized prompt that emphasizes generating the exact number."""
        return f"""Generate exactly {num_questions} {subject} multiple choice questions for {level} level students.

IMPORTANT: You must generate exactly {num_questions} complete questions.

Return only JSON array format:
[
{{"question":"What is 2+2?","options":["1","2","3","4"],"answer":"4"}},
{{"question":"What is 3+3?","options":["5","6","7","8"],"answer":"6"}}
]

Requirements:
- Exactly {num_questions} questions
- Each question must have 4 options
- Subject: {subject}
- Level: {level}
- Return only the JSON array, no other text"""