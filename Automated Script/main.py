import json
import requests

GEMINI_API_KEY = "AIzaSyDVW4vPFJ7frbYhklDgKoaE9-3CEka5Hpg"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

def gemini_generate(prompt):
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        response = requests.post(GEMINI_API_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"Gemini API error: {e}")
        return ""

def get_verified_field(prompt, field_name):
    while True:
        generated = gemini_generate(prompt)
        print(f"Gemini generated {field_name}:\n{generated}")
        user_action = input(f"Accept this {field_name}? (y to accept, n to retry, m to manually enter): ").strip().lower()
        if user_action == "y":
            return generated
        elif user_action == "m":
            return input(f"Enter {field_name} manually: ")
        # else retry

def collect_input():
    """
    This function collects hierarchical data for:
    - Branch -> Subject -> Test -> Question
    and writes it into a JSON file that matches your Django models.
    """
    data = []

    print("📘 START: Branch Data Collection")
    num_branches = int(input("Enter number of branches (int): "))
    for _ in range(num_branches):
        branch_name = input("Branch name (str): ")
        branch_desc = get_verified_field(f"Write a short description for the branch named '{branch_name}'.", "branch description")
        branch = {
            "name": branch_name,
            "description": branch_desc,
            "subjects": []
        }

        print(f"\n📗 Branch '{branch_name}' → Subjects")
        num_subjects = int(input(f"Enter number of subjects for {branch_name} (int): "))
        for _ in range(num_subjects):
            subject_name = input("  Subject name (str): ")
            subject_desc = get_verified_field(f"Write a short description for the subject named '{subject_name}' in branch '{branch_name}'.", "subject description")
            subject = {
                "name": subject_name,
                "description": subject_desc,
                "tests": []
            }

            print(f"\n📙 Subject '{subject_name}' → Tests")
            num_tests = int(input(f"  Enter number of tests for subject '{subject_name}' (int): "))
            for _ in range(num_tests):
                test_name = input("    Test name (str): ")
                duration = int(input("    Duration in minutes (int): "))
                total_marks = int(input("    Total marks (int): "))
                test = {
                    "name": test_name,
                    "duration_minutes": duration,
                    "total_marks": total_marks,
                    "questions": []
                }

                print(f"\n📝 Test '{test_name}' → Questions")
                num_questions = int(input(f"    Enter number of questions in test '{test_name}' (int): "))
                for i in range(num_questions):
                    print(f"      📄 Question {i+1}:")
                    question_text = input("        Question text (str): ")
                    options = [input(f"        Option {i} (str): ") for i in range(1, 5)]
                    correct_option = int(input("        Correct option (int, 1-4): "))
                    solution = get_verified_field(
                        f"Write a solution for the following question: '{question_text}' with options: {options}. The correct option is {correct_option}.",
                        "solution"
                    )
                    question = {
                        "text": question_text,
                        "option1": options[0],
                        "option2": options[1],
                        "option3": options[2],
                        "option4": options[3],
                        "correct_option": correct_option,
                        "solution": solution
                    }
                    test["questions"].append(question)
                subject["tests"].append(test)
            branch["subjects"].append(subject)
        data.append(branch)

    # Save to file
    with open("structured_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("\n✅ DONE: Data written to 'structured_data.json'")

# Run the script
if __name__ == "__main__":
    collect_input()
