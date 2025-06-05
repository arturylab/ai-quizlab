from app import app
from models import db, QuestionBank

def add_sample_questions():
    """
    Add sample questions to test the system.
    
    This function populates the question bank with basic test questions
    across different categories and levels for development testing.
    """
    with app.app_context():
        # Check if questions already exist to avoid duplicates
        existing_count = QuestionBank.query.count()
        if existing_count > 0:
            print(f"Questions already exist in database: {existing_count}")
            return

        # Sample questions for testing across different categories
        sample_questions = [
            {
                'category': 'Mathematics',
                'level': 'Elementary',
                'question': 'What is 2 + 2?',
                'option_a': '3',
                'option_b': '4',
                'option_c': '5',
                'option_d': '6',
                'correct_answer': '4'
            },
            {
                'category': 'Mathematics',
                'level': 'Elementary',
                'question': 'What is 5 - 3?',
                'option_a': '1',
                'option_b': '2',
                'option_c': '3',
                'option_d': '4',
                'correct_answer': '2'
            },
            {
                'category': 'Physics',
                'level': 'Elementary',
                'question': 'What is the speed of light?',
                'option_a': '300,000 km/s',
                'option_b': '150,000 km/s',
                'option_c': '450,000 km/s',
                'option_d': '600,000 km/s',
                'correct_answer': '300,000 km/s'
            },
            {
                'category': 'Computer Science',
                'level': 'Elementary',
                'question': 'What does CPU stand for?',
                'option_a': 'Computer Processing Unit',
                'option_b': 'Central Processing Unit',
                'option_c': 'Core Processing Unit',
                'option_d': 'Computer Program Unit',
                'correct_answer': 'Central Processing Unit'
            }
        ]

        # Add each question to the database
        for q_data in sample_questions:
            question = QuestionBank(**q_data)
            db.session.add(question)

        # Commit all changes to database
        db.session.commit()
        print(f"Added {len(sample_questions)} sample questions to the database!")

if __name__ == "__main__":
    add_sample_questions()