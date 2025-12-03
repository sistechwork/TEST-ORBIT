from main import app
from database import db
import models

def seed_questions():
    with app.app_context():
        existing_questions = models.Question.query.count()
        if existing_questions > 0:
            print(f"Database already has {existing_questions} questions. Skipping seed.")
            return
        
        default_password = models.AdminSettings.query.filter_by(setting_key='block_password').first()
        if not default_password:
            default_setting = models.AdminSettings(setting_key='block_password', setting_value='exam2024')
            db.session.add(default_setting)
            db.session.commit()
            print("Default block password set to 'exam2024'")
        
        questions_data = [
            {
                'question_type': 'MCQ',
                'question_text': 'What does HTML stand for?',
                'option_a': 'Hyper Text Markup Language',
                'option_b': 'High Tech Modern Language',
                'option_c': 'Home Tool Markup Language',
                'option_d': 'Hyperlinks and Text Markup Language',
                'correct_answer': 'A',
                'points': 1
            },
            {
                'question_type': 'MCQ',
                'question_text': 'Which programming language is known as the "language of the web"?',
                'option_a': 'Python',
                'option_b': 'JavaScript',
                'option_c': 'Java',
                'option_d': 'C++',
                'correct_answer': 'B',
                'points': 1
            },
            {
                'question_type': 'MCQ',
                'question_text': 'What does CSS stand for?',
                'option_a': 'Computer Style Sheets',
                'option_b': 'Creative Style Sheets',
                'option_c': 'Cascading Style Sheets',
                'option_d': 'Colorful Style Sheets',
                'correct_answer': 'C',
                'points': 1
            },
            {
                'question_type': 'MCQ',
                'question_text': 'Which of the following is a Python web framework?',
                'option_a': 'Django',
                'option_b': 'React',
                'option_c': 'Angular',
                'option_d': 'Vue',
                'correct_answer': 'A',
                'points': 1
            },
            {
                'question_type': 'MCQ',
                'question_text': 'What is the correct syntax to output "Hello World" in Python?',
                'option_a': 'echo "Hello World"',
                'option_b': 'printf("Hello World")',
                'option_c': 'print("Hello World")',
                'option_d': 'console.log("Hello World")',
                'correct_answer': 'C',
                'points': 1
            },
            {
                'question_type': 'MCQ',
                'question_text': 'Which HTTP method is used to send data to a server?',
                'option_a': 'GET',
                'option_b': 'POST',
                'option_c': 'DELETE',
                'option_d': 'PUT',
                'correct_answer': 'B',
                'points': 1
            },
            {
                'question_type': 'MCQ',
                'question_text': 'What does SQL stand for?',
                'option_a': 'Structured Query Language',
                'option_b': 'Simple Question Language',
                'option_c': 'Standard Query Language',
                'option_d': 'Structured Question Language',
                'correct_answer': 'A',
                'points': 1
            },
            {
                'question_type': 'MCQ',
                'question_text': 'Which of the following is NOT a valid data type in Python?',
                'option_a': 'int',
                'option_b': 'float',
                'option_c': 'char',
                'option_d': 'str',
                'correct_answer': 'C',
                'points': 1
            },
            {
                'question_type': 'MCQ',
                'question_text': 'What is the purpose of a database index?',
                'option_a': 'To make the database larger',
                'option_b': 'To speed up data retrieval',
                'option_c': 'To delete old records',
                'option_d': 'To encrypt data',
                'correct_answer': 'B',
                'points': 1
            },
            {
                'question_type': 'MCQ',
                'question_text': 'Which symbol is used for comments in Python?',
                'option_a': '//',
                'option_b': '/*',
                'option_c': '#',
                'option_d': '<!--',
                'correct_answer': 'C',
                'points': 1
            }
        ]
        
        for q_data in questions_data:
            question = models.Question(**q_data)
            db.session.add(question)
        
        db.session.commit()
        print(f"Successfully added {len(questions_data)} questions to the database!")

if __name__ == '__main__':
    seed_questions()
