# Static quiz questions for analytics practice
# These are easy-level questions for beginners

QUIZ_QUESTIONS = [
    {
        "id": 1,
        "topic": "Logical Reasoning",
        "difficulty": "Easy",
        "question": "If all roses are flowers and some flowers fade quickly, which statement is definitely true?",
        "options": [
            "All roses fade quickly",
            "Some roses are flowers",
            "All flowers are roses",
            "No roses fade quickly"
        ],
        "correct_answer": 1,  # Index of correct option (starts from 0)
        "explanation": "Since all roses are flowers, it's definitely true that some roses are flowers. We cannot conclude anything about fading from the given information."
    },
    {
        "id": 2,
        "topic": "Quantitative Aptitude",
        "difficulty": "Easy",
        "question": "A number is increased by 20% and then decreased by 20%. What is the net change?",
        "options": [
            "No change (0%)",
            "4% decrease",
            "4% increase",
            "2% decrease"
        ],
        "correct_answer": 1,
        "explanation": "Let's say the number is 100. After 20% increase: 120. After 20% decrease of 120: 120 - 24 = 96. Net change = 100 - 96 = 4% decrease."
    },
    {
        "id": 3,
        "topic": "Data Interpretation",
        "difficulty": "Easy",
        "question": "In a class of 50 students, 30 like Math and 25 like Science. If 10 students like both subjects, how many students like neither?",
        "options": [
            "5 students",
            "10 students",
            "15 students",
            "20 students"
        ],
        "correct_answer": 0,
        "explanation": "Students liking at least one subject = 30 + 25 - 10 = 45. Students liking neither = 50 - 45 = 5 students."
    },
    {
        "id": 4,
        "topic": "Logical Reasoning",
        "difficulty": "Easy",
        "question": "If in a certain code, COMPUTER is written as DPNQVUFS, how is SCIENCE written?",
        "options": [
            "TDJFODF",
            "SCJDMBD",
            "TDJFMDF",
            "RBHFMBD"
        ],
        "correct_answer": 0,
        "explanation": "Each letter is shifted by +1 in the alphabet. S→T, C→D, I→J, E→F, N→O, C→D, E→F. Answer: TDJFODF"
    },
    {
        "id": 5,
        "topic": "Quantitative Aptitude",
        "difficulty": "Easy",
        "question": "What is the average of first 10 natural numbers?",
        "options": [
            "5",
            "5.5",
            "6",
            "10"
        ],
        "correct_answer": 1,
        "explanation": "Sum of first 10 natural numbers = 10 × 11 / 2 = 55. Average = 55 / 10 = 5.5"
    },
    {
        "id": 6,
        "topic": "Pattern Recognition",
        "difficulty": "Easy",
        "question": "Find the next number in the series: 2, 6, 12, 20, 30, ?",
        "options": [
            "40",
            "42",
            "44",
            "38"
        ],
        "correct_answer": 1,
        "explanation": "Pattern: 1×2=2, 2×3=6, 3×4=12, 4×5=20, 5×6=30, 6×7=42. Each term is n×(n+1)."
    },
    {
        "id": 7,
        "topic": "Data Interpretation",
        "difficulty": "Easy",
        "question": "If 60% of a number is 120, what is 25% of that number?",
        "options": [
            "30",
            "40",
            "50",
            "60"
        ],
        "correct_answer": 2,
        "explanation": "60% of number = 120, so the number = 120/0.6 = 200. 25% of 200 = 50."
    },
    {
        "id": 8,
        "topic": "Logical Reasoning",
        "difficulty": "Easy",
        "question": "A is taller than B. C is shorter than B. Who is the shortest?",
        "options": [
            "A",
            "B",
            "C",
            "Cannot be determined"
        ],
        "correct_answer": 2,
        "explanation": "From the statements: A > B > C. Therefore, C is the shortest."
    },
    {
        "id": 9,
        "topic": "Quantitative Aptitude",
        "difficulty": "Easy",
        "question": "If the ratio of boys to girls in a class is 3:2 and there are 15 boys, how many girls are there?",
        "options": [
            "8",
            "10",
            "12",
            "15"
        ],
        "correct_answer": 1,
        "explanation": "Ratio is 3:2. If 3 parts = 15 boys, then 1 part = 5. So 2 parts (girls) = 2 × 5 = 10 girls."
    },
    {
        "id": 10,
        "topic": "Pattern Recognition",
        "difficulty": "Easy",
        "question": "Complete the series: A, C, F, J, O, ?",
        "options": [
            "T",
            "U",
            "S",
            "V"
        ],
        "correct_answer": 1,
        "explanation": "Pattern: +2, +3, +4, +5, +6. A→C(+2)→F(+3)→J(+4)→O(+5)→U(+6)."
    }
]


def get_all_questions():
    """Return all quiz questions"""
    return QUIZ_QUESTIONS


def get_question_by_id(question_id):
    """Get a specific question by ID"""
    for question in QUIZ_QUESTIONS:
        if question['id'] == question_id:
            return question
    return None