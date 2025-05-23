import os
from sqlalchemy import create_engine, text

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'my_secret_key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://postgres:postgres1234@localhost:5432/ai-quizlab'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

def test_connection():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("Database connection successful.")
    except Exception as e:
        print(f"Database connection failed: {e}")

if __name__ == "__main__":
    test_connection()