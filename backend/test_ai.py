import os
import sys


def main():
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

    import django
    django.setup()

    print("Testing Groq AI Question Generator...")
    print("=" * 60)

    try:
        from users.ai_generator import generate_questions

        print("\nGenerating 2 Logical Reasoning questions...")
        questions = generate_questions("Logical Reasoning", "Easy", 2)

        if questions and len(questions) > 0:
            print("\nSUCCESS! Question generation is working")
            print(f"Generated {len(questions)} questions")
            for i, q in enumerate(questions, 1):
                print("\n" + "=" * 60)
                print(f"QUESTION {i}:")
                print("=" * 60)
                print(f"Topic: {q['topic']}")
                print(f"Difficulty: {q['difficulty']}")
                print(f"Source: {q['source']}")
                print(f"\nQ: {q['question']}")
                print("\nOptions:")
                for j, opt in enumerate(q['options']):
                    marker = "✓" if j == q['correct_answer'] else " "
                    print(f"  [{marker}] {j+1}. {opt}")
                print(f"\nExplanation: {q['explanation']}")
        else:
            print("\nFAILED! No questions generated")

    except Exception as error:
        print(f"\nERROR: {error}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()