"""
Question Bank Migration Script
Imports question bank data from CSV export file.
"""

import os
import csv
from app import app
from models import db, QuestionBank

def check_database_connection():
    """Verify database connection is working."""
    try:
        with app.app_context():
            result = db.session.execute('SELECT 1')
            result.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def load_questions_from_csv():
    """Load questions from CSV file into database."""
    
    # Path to the CSV file
    csv_file = os.path.join('migrations', 'question_bank.csv')
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        print("💡 Make sure question_bank.csv exists in the migrations folder.")
        return False
    
    with app.app_context():
        # Check if questions already exist
        existing_count = QuestionBank.query.count()
        if existing_count > 0:
            print(f"⚠️  Question bank already contains {existing_count} questions.")
            response = input("Do you want to continue? This will add duplicate questions (y/N): ")
            if response.lower() != 'y':
                print("🛑 Migration cancelled.")
                return False
        
        try:
            print("📥 Reading questions from CSV file...")
            
            questions_added = 0
            with open(csv_file, 'r', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                
                for row_num, row in enumerate(csv_reader, 1):
                    # Skip header or empty rows
                    if len(row) < 9:
                        continue
                    
                    try:
                        # CSV format: id,question,option_a,option_b,option_c,option_d,correct_answer,category,level,timestamp
                        question_data = {
                            'question': row[1],
                            'option_a': row[2],
                            'option_b': row[3], 
                            'option_c': row[4],
                            'option_d': row[5],
                            'correct_answer': row[6],
                            'category': row[7],
                            'level': row[8]
                        }
                        
                        # Create new question
                        question = QuestionBank(**question_data)
                        db.session.add(question)
                        questions_added += 1
                        
                        # Progress indicator
                        if questions_added % 50 == 0:
                            print(f"   📊 Processed {questions_added} questions...")
                            
                    except Exception as e:
                        print(f"⚠️  Error processing row {row_num}: {e}")
                        continue
            
            # Commit all changes
            db.session.commit()
            
            # Verify import
            new_count = QuestionBank.query.count()
            imported_count = new_count - existing_count
            
            print(f"✅ Successfully imported {imported_count} questions!")
            
            # Show distribution summary
            show_question_distribution()
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during import: {e}")
            return False

def show_question_distribution():
    """Display question distribution by category and level."""
    
    categories = ['Mathematics', 'Physics', 'Chemistry', 'Biology', 'Computer Science']
    levels = ['Elementary', 'Middle School', 'High School']
    
    print("\n📊 Question Bank Distribution:")
    
    total_questions = 0
    for category in categories:
        category_count = QuestionBank.query.filter_by(category=category).count()
        if category_count > 0:
            print(f"  📚 {category}: {category_count} questions")
            total_questions += category_count
            
            for level in levels:
                level_count = QuestionBank.query.filter_by(category=category, level=level).count()
                if level_count > 0:
                    print(f"    - {level}: {level_count}")
    
    print(f"\n🎯 Total Questions Available: {total_questions}")

def main():
    """Run the question bank migration."""
    print("🚀 AI QuizLab - Question Bank Migration")
    print("=" * 50)
    
    # Check database connection
    if not check_database_connection():
        return
    
    # Ensure tables exist
    with app.app_context():
        db.create_all()
        print("✅ Database tables verified")
    
    # Load questions from CSV
    if load_questions_from_csv():
        print("\n🎉 Migration completed successfully!")
        print("💡 You can now create quizzes using the question bank.")
        print("🔧 Test by creating a quiz with 'Question Bank' sources enabled.")
    else:
        print("\n❌ Migration failed!")
        print("💡 Check the error messages above and try again.")

if __name__ == "__main__":
    main()