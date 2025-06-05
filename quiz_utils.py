import random
from models import QuestionBank


def load_questions_from_bank(subject, level, num_needed):
    """Load questions from the QuestionBank table in the database."""
    try:
        # Query the QuestionBank table
        all_matching_questions = QuestionBank.query.filter_by(
            category=subject, 
            level=level
        ).all()
        
        if not all_matching_questions:
            print(f"No questions found in DB for {subject} - {level}")
            return []

        # Shuffle them to get a random selection
        random.shuffle(all_matching_questions)
        
        # Select the number needed
        selected_db_questions = all_matching_questions[:num_needed]
        
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


def create_generation_report(stats, total_questions):
    """Create detailed generation report (simplified for bank-only)."""
    bank_count = stats['from_bank']
    failed = stats.get('failed_categories', [])
    
    # Calculate percentages
    bank_percent = 100 if total_questions > 0 else 0
    
    report = f"""✅ <strong>Quiz Generated Successfully!</strong><br><br>
📊 <strong>Generation Report:</strong><br>
📚 From Bank: <strong>{bank_count}</strong> questions ({bank_percent}%)<br>
📝 Total Questions: <strong>{total_questions}</strong><br>"""
    
    if failed:
        report += f"<br>⚠️ Categories with no questions found: {', '.join(failed)}"
    
    return report


def calculate_quiz_scores(quiz_questions, form_data):
    """Calculate scores for each category based on quiz answers."""
    categories = {
        'Mathematics': {'correct': 0, 'total': 0},
        'Physics': {'correct': 0, 'total': 0},
        'Chemistry': {'correct': 0, 'total': 0},
        'Biology': {'correct': 0, 'total': 0},
        'Computer Science': {'correct': 0, 'total': 0}
    }
    
    total_correct = 0
    
    for i, question in enumerate(quiz_questions):
        user_answer = form_data.get(f'q{i}')
        category = question.get('category', 'N/A')
        correct_answer = question.get('answer')
        
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
    """Create result data dictionary for database storage."""
    categories = scores['categories']
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
    """Format result summary for display."""
    return f"""
    <b>Results Summary:</b><br>
    Mathematics: {result_data['mathematics']}<br>
    Physics: {result_data['physics']}<br>
    Chemistry: {result_data['chemistry']}<br>
    Biology: {result_data['biology']}<br>
    Computer Science: {result_data['computer_science']}<br>
    <b>Total: {result_data['total']}</b>
    """