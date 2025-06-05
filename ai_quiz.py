import requests
import csv
import argparse
from datetime import datetime
import sys
import re
import tempfile
import os


class QuizGenerator:
    """
    Multiple choice quiz generator using Ollama AI.
    
    This class handles automated question generation via AI,
    parsing responses and saving them in CSV format.
    """
    
    def __init__(self, model: str = "phi3:mini", base_url: str = "http://localhost:11434/api/generate"):
        """
        Initialize the quiz generator.
        
        Args:
            model (str): Name of the Ollama model to use
            base_url (str): Base URL for Ollama API
        """
        self.model = model
        self.base_url = base_url

    def check_ollama_connection(self) -> bool:
        """
        Check if Ollama is running and accessible.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            response = requests.get(self.base_url.replace("/api/generate", "/api/tags"))
            return response.status_code == 200
        except Exception:
            return False

    def build_prompt(self, category: str, level: str, num_questions: int) -> str:
        """
        Build the prompt that will be sent to Ollama.
        
        Args:
            category (str): Quiz category (e.g., "Mathematics")
            level (str): Difficulty level (e.g., "Elementary", "High School")
            num_questions (int): Exact number of questions to generate
            
        Returns:
            str: Formatted prompt to send to AI
        """
        template = f"""
Generate exactly {num_questions} multiple choice questions about "{category}" appropriate for "{level}" level.

Format each question EXACTLY like this example:
Question: What is 2 + 2?
A) 3
B) 4
C) 5
D) 6
Answer: B

Question: What is 3 + 3?
A) 5
B) 6
C) 7
D) 8
Answer: B

Rules:
- Generate exactly {num_questions} questions
- Each question must have exactly 4 options labeled A), B), C), D)
- Provide the correct answer as A, B, C, or D
- Questions should be appropriate for {level} level
- Focus only on {category} topics
- Use the exact format shown above
- Each question should be separated by a blank line

Generate {num_questions} questions now:
"""
        return template.strip()

    def call_api(self, prompt: str) -> str:
        """
        Make API call to Ollama and return the complete text response.
        
        Args:
            prompt (str): The prompt to send to the AI model
            
        Returns:
            str: Generated text response from AI
            
        Raises:
            ConnectionError: If unable to connect to Ollama
            ValueError: If response format is invalid
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            response_data = response.json()
            return response_data.get("response", "")
            
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error connecting to Ollama: {e}")
        except Exception as e:
            raise ValueError(f"Invalid response from Ollama: {e}")

    def parse_questions(self, raw_text: str) -> list:
        """
        Parse questions from AI text format into structured data.
        
        Args:
            raw_text (str): Raw text response from AI containing questions
            
        Returns:
            list: List of dictionaries containing parsed question data
        """
        questions = []
        
        # Split text into sections by double newlines or question patterns
        sections = re.split(r'\n\s*\n|\n(?=Question:)', raw_text)
        
        for section in sections:
            section = section.strip()
            if not section or 'Question:' not in section:
                continue
            
            try:
                # Extract question text
                question_match = re.search(r'Question:\s*(.+?)(?=\n[A-D]\))', section, re.DOTALL)
                if not question_match:
                    continue
                question_text = question_match.group(1).strip()
                
                # Extract all options (A, B, C, D)
                options = []
                option_texts = []
                for letter in ['A', 'B', 'C', 'D']:
                    option_match = re.search(f'{letter}\\)\\s*(.+?)(?=\\n[A-D]\\)|\\nAnswer:|$)', section, re.DOTALL)
                    if option_match:
                        option_text = option_match.group(1).strip()
                        options.append(letter)
                        option_texts.append(option_text)
                
                # Validate that we have exactly 4 options
                if len(options) != 4:
                    continue
                
                # Extract correct answer
                answer_match = re.search(r'Answer:\s*([A-D])', section)
                if not answer_match:
                    continue
                answer_letter = answer_match.group(1)
                
                # Find the corresponding answer text
                if answer_letter in options:
                    answer_index = options.index(answer_letter)
                    answer_text = option_texts[answer_index]
                else:
                    continue
                
                # Create structured question data
                question_data = {
                    'question': question_text,
                    'option_a': option_texts[0] if len(option_texts) > 0 else '',
                    'option_b': option_texts[1] if len(option_texts) > 1 else '',
                    'option_c': option_texts[2] if len(option_texts) > 2 else '',
                    'option_d': option_texts[3] if len(option_texts) > 3 else '',
                    'correct_answer': answer_text,
                    'answer_letter': answer_letter
                }
                
                questions.append(question_data)
                
            except Exception as e:
                print(f"Error parsing question: {e}")
                continue
        
        return questions

    def validate_questions(self, questions: list, category: str, level: str) -> list:
        """
        Validate and clean the questions list, adding metadata.
        
        Args:
            questions (list): List of parsed question dictionaries
            category (str): Quiz category to add as metadata
            level (str): Difficulty level to add as metadata
            
        Returns:
            list: List of validated questions with added metadata
        """
        validated = []
        
        for i, question in enumerate(questions):
            if not isinstance(question, dict):
                continue
            
            # Check that all required fields exist and are not empty
            required_fields = ['question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer']
            if not all(field in question and question[field].strip() for field in required_fields):
                continue
            
            # Add category and level metadata
            question['category'] = category
            question['level'] = level
            
            validated.append(question)
        
        return validated

    def generate_quiz(self, num_questions: int, category: str, level: str, max_attempts: int = 3) -> list:
        """
        Generate the requested number of questions with retry logic.
        
        Args:
            num_questions (int): Number of questions to generate
            category (str): Subject category for questions
            level (str): Difficulty level
            max_attempts (int): Maximum number of attempts if generation fails
            
        Returns:
            list: List of generated and validated questions
            
        Raises:
            ConnectionError: If unable to connect to Ollama
        """
        # Verify Ollama connection before starting
        if not self.check_ollama_connection():
            raise ConnectionError("❌ Could not connect to Ollama at: " + self.base_url)

        accumulated_questions = []
        attempts = 0
        
        # Retry logic to ensure we get the requested number of questions
        while len(accumulated_questions) < num_questions and attempts < max_attempts:
            attempts += 1
            missing_questions = num_questions - len(accumulated_questions)
            
            # Progress messaging
            if attempts == 1:
                print(f"🔍 Generating {num_questions} questions about '{category}' at '{level}' level...")
            else:
                print(f"⚠️  Only {len(accumulated_questions)} questions generated. Requesting {missing_questions} more (attempt {attempts})...")
            
            # Generate new questions
            prompt = self.build_prompt(category, level, missing_questions)
            raw_response = self.call_api(prompt)
            new_questions = self.parse_questions(raw_response)
            validated_questions = self.validate_questions(new_questions, category, level)
            
            # Add only unique questions to avoid duplicates
            for question in validated_questions:
                if len(accumulated_questions) >= num_questions:
                    break
                if not any(question['question'].lower() == existing['question'].lower() for existing in accumulated_questions):
                    accumulated_questions.append(question)
        
        # Warning if we couldn't generate enough questions
        if len(accumulated_questions) < num_questions:
            print(f"⚠️  Warning: only {len(accumulated_questions)} questions generated out of {num_questions} requested.")
        
        return accumulated_questions[:num_questions]

    def save_quiz_csv(self, questions: list, filename: str = None) -> str:
        """
        Save the questions list to a CSV file.
        
        Args:
            questions (list): List of question dictionaries to save
            filename (str, optional): Output filename. If None, timestamp will be used
            
        Returns:
            str: Path to the saved CSV file
        """
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"quiz_{timestamp}.csv"
        elif not filename.endswith('.csv'):
            filename += '.csv'

        # Define CSV headers
        headers = ['question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'answer_letter', 'category', 'level']
        
        # Write questions to CSV file
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            
            for question in questions:
                writer.writerow(question)
        
        print(f"✅ Quiz saved to: {filename}")
        return filename

    def generate_and_save_temp_csv(self, categories_requests: list) -> str:
        """
        Generate questions for multiple categories and save to a temporary CSV file.
        
        Args:
            categories_requests (list): List of tuples (category, level, num_questions)
            
        Returns:
            str: Path to the temporary CSV file
            
        Raises:
            Exception: If question generation fails for any category
        """
        all_questions = []
        
        # Generate questions for each requested category
        for category, level, num_questions in categories_requests:
            print(f"🔍 Generating {num_questions} questions for {category} at {level} level...")
            questions = self.generate_quiz(num_questions, category, level)
            all_questions.extend(questions)
        
        # Create temporary file for CSV output
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
        temp_path = temp_file.name
        temp_file.close()  # Close the file handle immediately
        
        # Define CSV headers
        headers = ['question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'answer_letter', 'category', 'level']
        
        # Write all questions to temporary CSV file
        with open(temp_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            
            for question in all_questions:
                writer.writerow(question)
        
        print(f"✅ Generated {len(all_questions)} total questions saved to temporary file: {temp_path}")
        return temp_path


def main():
    """
    Command-line interface for the quiz generator.
    Handles argument parsing and orchestrates the quiz generation process.
    """
    parser = argparse.ArgumentParser(description="Multiple choice question generator using Ollama - CSV format")
    parser.add_argument("-q", "--questions", type=int, default=5, 
                        help="Number of questions (default: 5)")
    parser.add_argument("-c", "--category",
                        choices=["mathematics", "physics", "chemistry", "biology", "computer science"],
                        required=True,
                        help="Quiz category")
    parser.add_argument("-l", "--level",
                        choices=["Elementary", "Middle School", "High School"],
                        default="Elementary",
                        help="Difficulty level: Elementary, Middle School or High School (default: Elementary)")
    parser.add_argument("-o", "--output",
                        help="Output filename (e.g.: my_quiz.csv). If not specified, timestamp will be used.")

    args = parser.parse_args()

    try:
        # Initialize generator and create quiz
        generator = QuizGenerator()
        questions = generator.generate_quiz(args.questions, args.category, args.level)

        if questions:
            # Save questions to CSV file
            filename = generator.save_quiz_csv(questions, filename=args.output)
            
            # Display success summary
            print(f"\n📋 Successfully generated {len(questions)} questions.")
            print(f"📁 File: {filename}")
            print(f"📊 Format: CSV with columns - question, option_a, option_b, option_c, option_d, correct_answer, answer_letter, category, level")
        else:
            print("❌ Could not generate valid questions.")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
