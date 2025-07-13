from django.core.management.base import BaseCommand
from django.db import transaction
from Test_Interface.models import Branch, Subject, Test, Question
import json
import os

class Command(BaseCommand):
    help = 'Import questions from a JSON file with nested structure (Branch -> Subject -> Test -> Questions)'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file containing questions')
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing questions if they already exist',
        )

    def handle(self, *args, **options):
        json_file_path = options['json_file']
        update_existing = options['update_existing']

        if not os.path.exists(json_file_path):
            self.stderr.write(self.style.ERROR(f'File not found: {json_file_path}'))
            return

        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except json.JSONDecodeError as e:
            self.stderr.write(self.style.ERROR(f'Invalid JSON file: {str(e)}'))
            return
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error reading file: {str(e)}'))
            return

        self.import_data(data, update_existing)

    @transaction.atomic
    def import_data(self, data, update_existing):
        total_questions = 0
        updated_questions = 0
        new_questions = 0

        for branch_data in data:
            branch_name = branch_data.get('name')
            if not branch_name:
                self.stderr.write(self.style.WARNING('Skipping branch with no name'))
                continue

            branch, _ = Branch.objects.get_or_create(
                name=branch_name,
                defaults={'description': branch_data.get('description', '')}
            )
            self.stdout.write(f'Processing branch: {branch.name}')

            for subject_data in branch_data.get('subjects', []):
                subject_name = subject_data.get('name')
                if not subject_name:
                    self.stderr.write(self.style.WARNING(f'Skipping subject with no name in branch {branch.name}'))
                    continue

                subject, _ = Subject.objects.get_or_create(
                    name=subject_name,
                    branch=branch,
                    defaults={'description': subject_data.get('description', '')}
                )
                self.stdout.write(f'  Processing subject: {subject.name}')

                for test_data in subject_data.get('tests', []):
                    test_name = test_data.get('name')
                    if not test_name:
                        self.stderr.write(self.style.WARNING(f'Skipping test with no name in subject {subject.name}'))
                        continue

                    test, _ = Test.objects.get_or_create(
                        name=test_name,
                        subject=subject,
                        defaults={
                            'duration_minutes': test_data.get('duration_minutes', 60),
                            'total_marks': test_data.get('total_marks', 100)
                        }
                    )
                    self.stdout.write(f'    Processing test: {test.name}')

                    for question_data in test_data.get('questions', []):
                        total_questions += 1
                        try:
                            # Validate required fields
                            required_fields = ['text', 'option1', 'option2', 'option3', 'option4', 'correct_option']
                            if not all(question_data.get(field) for field in required_fields):
                                self.stderr.write(
                                    self.style.WARNING(f'Skipping question with missing required fields in test {test.name}')
                                )
                                continue

                            # Try to find existing question
                            existing_question = Question.objects.filter(
                                test=test,
                                text=question_data['text']
                            ).first()

                            if existing_question and not update_existing:
                                self.stdout.write(f'      Skipping existing question: {question_data["text"][:50]}...')
                                continue

                            question_fields = {
                                'text': question_data['text'],
                                'option1': question_data['option1'],
                                'option2': question_data['option2'],
                                'option3': question_data['option3'],
                                'option4': question_data['option4'],
                                'correct_option': int(question_data['correct_option']),
                                'solution': question_data.get('solution', '')
                            }

                            if existing_question and update_existing:
                                for key, value in question_fields.items():
                                    setattr(existing_question, key, value)
                                existing_question.save()
                                updated_questions += 1
                                self.stdout.write(f'      Updated question: {question_data["text"][:50]}...')
                            else:
                                Question.objects.create(test=test, **question_fields)
                                new_questions += 1
                                self.stdout.write(f'      Created new question: {question_data["text"][:50]}...')

                        except Exception as e:
                            self.stderr.write(
                                self.style.ERROR(f'Error processing question in test {test.name}: {str(e)}')
                            )

        # Print summary
        self.stdout.write(self.style.SUCCESS(f'''
Import completed:
Total questions processed: {total_questions}
New questions added: {new_questions}
Questions updated: {updated_questions}
        '''))
