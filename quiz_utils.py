import random
import csv
import os
import tempfile
from models import QuestionBank

# ============================================================================
# QUESTION BANK UTILITIES
# ============================================================================

def load_questions_from_bank(subject, level, num_needed):
    """
    Load questions from the QuestionBank table in the database.
    
    Args:
        subject (str): Subject category (e.g., "Mathematics", "Physics")
        level (str): Difficulty level (e.g., "Elementary", "High School")
        num_needed (int): Number of questions to retrieve
        
    Returns:
        list: List of formatted question dictionaries ready for quiz creation
    """
    try:
        # Query the QuestionBank table for matching criteria
        all_matching_questions = QuestionBank.query.filter_by(
            category=subject, 
            level=level
        ).all()
        
        if not all_matching_questions:
            print(f"No questions found in DB for {subject} - {level}")
            return []

        # Shuffle questions to get random selection
        random.shuffle(all_matching_questions)
        
        # Select the required number of questions
        selected_db_questions = all_matching_questions[:num_needed]
        
        # Format questions for compatibility with existing system
        formatted_questions = []
        for i, db_q in enumerate(selected_db_questions):
            formatted_q = {
                'id': f"BANK-{db_q.id}",
                'question': db_q.question,
                'options': [
                    db_q.option_a, 
                    db_q.option_b, 
                    db_q.option_c, 
                    db_q.option_d
                ],
                'answer': db_q.correct_answer,
                'category': db_q.category,
                'level': db_q.level,
                'source': 'BANK'
            }
            formatted_questions.append(formatted_q)
        
        print(f"Loaded {len(formatted_questions)} questions from DB for {subject} - {level}")
        return formatted_questions
        
    except Exception as e:
        print(f"Error loading questions from database bank: {e}")
        return []

# ============================================================================
# AI QUIZ PROCESSING UTILITIES
# ============================================================================

def parse_ai_csv_to_quiz_questions(csv_file_path, quiz_id):
    """
    Parse AI-generated CSV and convert directly to QuizQuestion objects.
    
    Args:
        csv_file_path (str): Path to the AI-generated CSV file
        quiz_id (int): ID of the quiz to associate questions with
        
    Returns:
        list: List of QuizQuestion objects ready for database insertion
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        Exception: If CSV parsing fails
    """
    from models import QuizQuestion  # Import here to avoid circular imports
    
    quiz_questions = []
    
    try:
        # Validate file existence
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        # Parse CSV file and create QuizQuestion objects
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for i, row in enumerate(reader):
                # Validate required fields are present and not empty
                required_fields = ['question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'category', 'level']
                if not all(field in row and row[field].strip() for field in required_fields):
                    print(f"Skipping invalid row {i+1}: Missing required fields")
                    continue
                
                # Create QuizQuestion object directly from CSV data
                quiz_question = QuizQuestion(
                    quiz_id=quiz_id,
                    question=row['question'].strip(),
                    option_a=row['option_a'].strip(),
                    option_b=row['option_b'].strip(),
                    option_c=row['option_c'].strip(),
                    option_d=row['option_d'].strip(),
                    correct_answer=row['correct_answer'].strip(),
                    category=row['category'].strip(),
                    level=row['level'].strip(),
                    source='AI',
                    order_index=i
                )
                
                quiz_questions.append(quiz_question)
        
        print(f"✅ Parsed {len(quiz_questions)} AI questions from CSV")
        
    except Exception as e:
        print(f"❌ Error parsing AI CSV: {e}")
        raise
    
    finally:
        # Clean up temporary file to free disk space
        try:
            if os.path.exists(csv_file_path):
                os.unlink(csv_file_path)
                print(f"✅ Cleaned up temporary CSV file: {csv_file_path}")
        except Exception as e:
            print(f"⚠️ Warning: Could not delete temporary file {csv_file_path}: {e}")
    
    return quiz_questions

# ============================================================================
# REPORTING UTILITIES
# ============================================================================

def create_generation_report(stats, total_questions):
    """
    Create detailed generation report for quiz creation results.
    
    Args:
        stats (dict): Statistics dictionary containing generation counts
        total_questions (int): Total number of questions generated
        
    Returns:
        str: HTML-formatted report string for display
    """
    bank_count = stats.get('from_bank', 0)
    ai_count = stats.get('from_ai', 0)
    failed = stats.get('failed_categories', [])
    
    # Calculate percentages for better user understanding
    bank_percent = (bank_count / total_questions * 100) if total_questions > 0 else 0
    ai_percent = (ai_count / total_questions * 100) if total_questions > 0 else 0
    
    # Build HTML report with detailed breakdown
    report = f"""✅ <strong>Quiz Generated Successfully!</strong><br><br>
📊 <strong>Generation Report:</strong><br>"""
    
    if bank_count > 0:
        report += f"📚 From Bank: <strong>{bank_count}</strong> questions ({bank_percent:.1f}%)<br>"
    
    if ai_count > 0:
        report += f"🤖 From AI: <strong>{ai_count}</strong> questions ({ai_percent:.1f}%)<br>"
    
    report += f"📝 Total Questions: <strong>{total_questions}</strong><br>"
    
    # Add warning for failed categories if any
    if failed:
        report += f"<br>⚠️ Categories with no questions found: {', '.join(failed)}"
    
    return report

# ============================================================================
# QUIZ SCORING UTILITIES
# ============================================================================

def calculate_quiz_scores(quiz_questions, form_data):
    """
    Calculate scores for each category based on student's quiz answers.
    
    Args:
        quiz_questions (list): List of quiz question dictionaries
        form_data (dict): Form data containing student's answers
        
    Returns:
        dict: Scores organized by category with totals
    """
    # Initialize scoring structure for all supported categories
    categories = {
        'Mathematics': {'correct': 0, 'total': 0},
        'Physics': {'correct': 0, 'total': 0},
        'Chemistry': {'correct': 0, 'total': 0},
        'Biology': {'correct': 0, 'total': 0},
        'Computer Science': {'correct': 0, 'total': 0}
    }
    
    total_correct = 0
    
    # Process each question and compare with student's answer
    for i, question in enumerate(quiz_questions):
        user_answer = form_data.get(f'q{i}')
        category = question.get('category', 'N/A')
        correct_answer = question.get('answer')
        
        # Update category statistics
        if category in categories:
            categories[category]['total'] += 1
            if user_answer == correct_answer:
                categories[category]['correct'] += 1
                total_correct += 1
    
    return {
        'categories': categories,
        'total_correct': total_correct,
        'total_questions': len(quiz_questions)
    }

def create_result_data(student, scores):
    """
    Create result data dictionary for database storage.
    
    Args:
        student (Student): Student object containing student information
        scores (dict): Calculated scores from calculate_quiz_scores()
        
    Returns:
        dict: Formatted result data ready for Result model creation
    """
    categories = scores['categories']
    
    # Format scores as "correct/total" strings for database storage
    return {
        'student_id': student.id,
        'name': student.name,
        'group': student.group,
        'mathematics': f"{categories['Mathematics']['correct']}/{categories['Mathematics']['total']}",
        'physics': f"{categories['Physics']['correct']}/{categories['Physics']['total']}",
        'chemistry': f"{categories['Chemistry']['correct']}/{categories['Chemistry']['total']}",
        'biology': f"{categories['Biology']['correct']}/{categories['Biology']['total']}",
        'computer_science': f"{categories['Computer Science']['correct']}/{categories['Computer Science']['total']}",
        'total': f"{scores['total_correct']}/{scores['total_questions']}"
    }

def format_result_summary(result_data):
    """
    Format result summary for user-friendly display.
    
    Args:
        result_data (dict): Result data dictionary from create_result_data()
        
    Returns:
        str: HTML-formatted summary string for display
    """
    return f"""
    <b>Results Summary:</b><br>
    Mathematics: {result_data['mathematics']}<br>
    Physics: {result_data['physics']}<br>
    Chemistry: {result_data['chemistry']}<br>
    Biology: {result_data['biology']}<br>
    Computer Science: {result_data['computer_science']}<br>
    <b>Total: {result_data['total']}</b>
    """