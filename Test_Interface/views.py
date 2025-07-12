# Test_Interface/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Avg, Count, F, Case, When, Value, CharField, IntegerField, Max
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.conf import settings
import io
import base64
import requests
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
import os
from dotenv import load_dotenv
from .models import Branch, Subject, Test, Question, UserAttempt, UserProfile
from .forms import BranchSelectionForm, UserProfileForm, AccountSettingsForm
import certifi

load_dotenv()  # Load environment variables from .env file

def upload_image_to_external_api(image_file):
    """
    Uploads an image to imgbb.com and returns the hosted image URL.
    """
    if not image_file:
        return None

    try:
        import base64
        import requests
        import os
        from django.conf import settings
        
        # Get API key from settings or environment
        api_key = getattr(settings, 'IMGBB_API_KEY', os.getenv('IMGBB_API_KEY'))
        if not api_key:
            print("Warning: IMGBB_API_KEY not found in settings or environment variables")
            return None

        # Read and encode image as base64
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        # Prepare API endpoint and payload
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": api_key,
            "image": encoded_image
        }

        # Send POST request
        response = requests.post(url, data=payload)
        response.raise_for_status()  # Raise if error (4xx/5xx)
        
        # Parse response
        data = response.json()
        if data.get('success'):
            return data['data']['url']
        else:
            print(f"Image upload failed: {data.get('error', 'Unknown error')}")
            return None

    except Exception as e:
        print(f"Error uploading image: {str(e)}")
        return None

        # Extract image URL from response JSON
        data = response.json()
        print(f"Image uploaded successfully: {data['data']['url']}")
        return data['data']['url']

    except Exception as e:
        print(f"Image upload failed: {e}")
        return None

@login_required(login_url='/login/')
def branch_selection_view(request):
    """
    Allows the user to select their engineering branch.
    Redirects to dashboard if branch is already selected.
    """
    user_profile = request.user.profile
    if user_profile.branch and request.method == 'GET':
        messages.info(request, f"Your current branch is {user_profile.branch.name}.")
        return redirect('dashboard') # Already has a branch, go to dashboard

    if request.method == 'POST':
        form = BranchSelectionForm(request.POST)
    else:
        # Pre-fill with current user branch if exists
        form = BranchSelectionForm(initial={
        'branch': user_profile.branch if user_profile.branch else None
    })

    if request.method == 'POST':
        if form.is_valid():
            selected_branch = form.cleaned_data['branch']
            user_profile.branch = selected_branch
            user_profile.save()
            messages.success(request, f"Your branch has been set to {selected_branch.name}.")
            return redirect('dashboard')
        else:
            messages.error(request, "Please select a valid branch.")

    branches = Branch.objects.all().order_by('name') # For displaying options if form fails or for initial GET
    return render(request, 'Test_Interface/branch_selection.html', {'form': form, 'branches': branches,'is_mobile': request.user_agent.is_mobile})

@login_required(login_url='/login/')
def dashboard_view(request):
    """
    Main dashboard showing subjects and tests relevant to the user's branch.
    If no branch is selected, redirects to branch selection.
    """

    user_profile = request.user.profile
    if not user_profile.branch:
        messages.warning(request, "Please select your engineering branch to view subjects and tests.")
        return redirect('branch_selection')

    if request.method == 'POST':
        form = BranchSelectionForm(request.POST)
    else:
        # Pre-fill with current user branch if exists
        form = BranchSelectionForm(initial={
        'branch': user_profile.branch if user_profile.branch else None
    })

    if request.method == 'POST':
        if form.is_valid():
            selected_branch = form.cleaned_data['branch']
            user_profile.branch = selected_branch
            user_profile.save()
            messages.success(request, f"Your branch has been set to {selected_branch.name}.")
            return redirect('dashboard')
        else:
            messages.error(request, "Please select a valid branch.")



    # Fetch subjects for the user's selected branch
    subjects = Subject.objects.filter(branch=user_profile.branch).prefetch_related('tests').order_by('name')

    # Prepare tests with attempt status
    tests_with_status = []
    for subject in subjects:
        for test in subject.tests.all():
            # Check if user has any attempt for this test
            has_attempted = UserAttempt.objects.filter(user=request.user, question__test=test).exists()
            
            # Get the latest score if attempted
            latest_score = None
            if has_attempted:
                # Calculate score for the latest completed attempt of this test
                # This assumes a test is "completed" if all questions have an attempt record
                total_questions_in_test = test.questions.count()
                user_attempts_for_test = UserAttempt.objects.filter(user=request.user, question__test=test)
                
                if user_attempts_for_test.count() == total_questions_in_test:
                    correct_attempts = user_attempts_for_test.filter(is_correct=True).count()
                    latest_score = f"{int((correct_attempts / total_questions_in_test) * 100)}%" if total_questions_in_test else "0%"
                else:
                    # If not all questions attempted, consider it "In Progress" or partial
                    latest_score = "In Progress"

            tests_with_status.append({
                'test': test,
                'has_attempted': has_attempted,
                'latest_score': latest_score,
            })
    
    # Group tests by subject for display in the template
    subjects_with_tests = []
    for subject in subjects:
        subject_tests = [ts for ts in tests_with_status if ts['test'].subject == subject]
        subjects_with_tests.append({
            'subject': subject,
            'tests': subject_tests
        })
    
    
    branches = Branch.objects.all().order_by('name')
    form = BranchSelectionForm(request.POST or None)

    return render(request, 'Test_Interface/test_dashboard.html', {
        'form': form,
        'branches': branches,
        'user_branch': user_profile.branch,
        'subjects_with_tests': subjects_with_tests,
        'is_mobile': request.user_agent.is_mobile,
    })

@login_required(login_url='/login/')
def start_test(request, test_id):
    """
    Initializes a new test attempt for the user.
    Instead of deleting previous attempts, it creates a new attempt session,
    allowing the user to attempt the same test multiple times.
    """
    test = get_object_or_404(Test, id=test_id)

    # Optionally, you can create a TestAttempt model to track each session.
    # For now, we just keep all UserAttempt records and start a new run.
    # The question_view logic should be able to distinguish between attempts if you add a session key.

    messages.info(request, f"Starting new test: {test.name} in {test.subject.name}. (Multiple attempts allowed)")
    return redirect('question_view', test_id=test.id, q_index=0)

@login_required(login_url='/login/')
def question_view(request, test_id, q_index=0):
    test = get_object_or_404(Test, id=test_id)
    subject = test.subject
    questions = list(test.questions.all().order_by('id'))

    total_questions = len(questions)
    answered_questions = UserAttempt.objects.filter(
        user=request.user,
        question__test=test
    ).count()
    all_questions_answered = (answered_questions == total_questions)

    # Compute test end time and remaining duration
    end_time = test.created_at + timedelta(minutes=test.duration_minutes)
    now = timezone.now()
    time_remaining = end_time - now
    test_active = (time_remaining.total_seconds() > 0) and (q_index < total_questions)

    if q_index >= total_questions:
        messages.info(request, "Test completed! Calculating your results...")
        return redirect('display_test_result', test_id=test.id)

    question = questions[q_index]
    submitted = False
    is_correct = None
    selected_option_value = None

    if request.method == 'POST':
        is_review = request.POST.get('is_review') == '1'
        selected_option_value = request.POST.get('option')

        if not is_review and selected_option_value is None:
            messages.error(request, "Please select an option before submitting.")
            current_attempt = UserAttempt.objects.filter(user=request.user, question=question).first()
            if current_attempt:
                submitted = True
                is_correct = current_attempt.is_correct
                selected_option_value = current_attempt.selected_option
            return render(request, 'Test_Interface/question.html', {
                'subject': subject,
                'test': test,
                'question': question,
                'q_index': q_index,
                'total': total_questions,
                'submitted': submitted,
                'is_correct': is_correct,
                'solution': question.solution,
                'selected': selected_option_value,
                'all_questions_answered': all_questions_answered,
                'test_active': test_active,
                'time_remaining': time_remaining,
                'is_mobile': request.user_agent.is_mobile,
            })

        if not is_review:
            try:
                selected_option_value = int(selected_option_value)
            except ValueError:
                messages.error(request, "Invalid option selected.")
                current_attempt = UserAttempt.objects.filter(user=request.user, question=question).first()
                if current_attempt:
                    submitted = True
                    is_correct = current_attempt.is_correct
                    selected_option_value = current_attempt.selected_option
                return render(request, 'Test_Interface/question.html', {
                    'subject': subject,
                    'test': test,
                    'question': question,
                    'q_index': q_index,
                    'total': total_questions,
                    'submitted': submitted,
                    'is_correct': is_correct,
                    'solution': question.solution,
                    'selected': selected_option_value,
                    'all_questions_answered': all_questions_answered,
                    'test_active': test_active,
                    'time_remaining': time_remaining,
                    'is_mobile': request.user_agent.is_mobile,
                })

            is_correct = (selected_option_value == question.correct_option)

            UserAttempt.objects.update_or_create(
                user=request.user,
                question=question,
                defaults={
                    'selected_option': selected_option_value,
                    'is_correct': is_correct,
                    'reviewed': False
                }
            )
            submitted = True

            if is_correct:
                messages.success(request, "Correct answer!")
            else:
                messages.error(request, f"Incorrect. The correct answer was option {question.correct_option}.")
        else:
            UserAttempt.objects.update_or_create(
                user=request.user,
                question=question,
                defaults={
                    'selected_option': None,
                    'is_correct': False,
                    'reviewed': True
                }
            )
            messages.info(request, "Question marked for review.")

        if q_index + 1 < total_questions:
            return redirect('question_view', test_id=test.id, q_index=q_index + 1)
        else:
            return redirect('display_test_result', test_id=test.id)

    current_attempt = UserAttempt.objects.filter(
        user=request.user,
        question=question
    ).first()

    if current_attempt:
        submitted = True
        is_correct = current_attempt.is_correct
        selected_option_value = current_attempt.selected_option

    return render(request, 'Test_Interface/question.html', {
        'subject': subject,
        'test': test,
        'question': question,
        'q_index': q_index,
        'total': total_questions,
        'submitted': submitted,
        'is_correct': is_correct,
        'solution': question.solution,
        'selected': selected_option_value,
        'all_questions_answered': all_questions_answered,
        'test_active': test_active,
        'time_remaining': time_remaining,
        'is_mobile': request.user_agent.is_mobile,
    })

@login_required(login_url='/login/')
def display_test_result(request, test_id):
    """
    Calculates and displays the results for a completed test.
    """
    test = get_object_or_404(Test, id=test_id)
    subject = test.subject

    user_attempts = UserAttempt.objects.filter(user=request.user, question__test=test)
    total_questions_in_test = test.questions.count()
    total_questions_attempted = user_attempts.count()
    correct_answers = user_attempts.filter(is_correct=True).count()

    percent_correct = int((correct_answers / total_questions_in_test) * 100) if total_questions_in_test else 0

    return render(request, 'Test_Interface/result.html', {
        'subject': subject,
        'test': test,
        'total_in_test': total_questions_in_test,
        'total_attempted': total_questions_attempted,
        'correct': correct_answers,
        'percent': percent_correct,
        'is_mobile': request.user_agent.is_mobile,
    })

@login_required(login_url='/login/')
def user_history_view(request):
    """
    Displays the user's test history, including scores for completed tests.
    """
    # Get all distinct tests the user has attempted questions for
    # Annotate with total questions in test and correct answers for that test
    # This query aggregates results for each test
    user_test_results = UserAttempt.objects.filter(user=request.user) \
        .values('question__test__id', 'question__test__name', 'question__test__subject__name', 'question__test__total_marks') \
        .annotate(
            total_attempted_questions=Count('question__id'),
            correct_answers=Count(Case(When(is_correct=True, then=1), output_field=IntegerField())),

            latest_attempt_date= Max('attempted_at')
        ) \
        .order_by('-latest_attempt_date') # Order by most recent attempt

    # Further process to get total questions for each test and calculate percentage
    history_data = []
    for result in user_test_results:
        test_id = result['question__test__id']
        test_name = result['question__test__name']
        subject_name = result['question__test__subject__name']
        total_test_questions = Test.objects.get(id=test_id).questions.count() # Get total questions for this test
        total_marks = result['question__test__total_marks']

        score_percent = 0
        if total_test_questions > 0:
            score_percent = int((result['correct_answers'] / total_test_questions) * 100)

        # Determine if test is "completed" (all questions attempted)
        status = "Completed" if result['total_attempted_questions'] == total_test_questions else "In Progress"

        history_data.append({
            'test_name': test_name,
            'subject_name': subject_name,
            'total_questions': total_test_questions,
            'total_attempted': result['total_attempted_questions'],
            'correct_answers': result['correct_answers'],
            'score_percent': score_percent,
            'status': status,
            'attempt_date': result['latest_attempt_date'],
            'test_id': test_id, # Add test_id for linking to results page
            'total_marks': total_marks,
        })

    return render(request, 'Test_Interface/history.html', {'history_data': history_data, 'is_mobile': request.user_agent.is_mobile})

@login_required(login_url='/login/')
def user_profile_view(request):
    user = request.user
    user_profile = user.profile

    if request.method == 'POST':
        # Check if this is just a profile picture upload
        if 'profile_picture_upload' in request.FILES:
            profile_picture_file = request.FILES['profile_picture_upload']
            
            # Validate file type
            allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
            if profile_picture_file.content_type not in allowed_types:
                messages.error(request, "Please upload only JPEG or PNG images.")
                return redirect('user_dashboard')
                
            # Validate file size (max 5MB)
            if profile_picture_file.size > 5 * 1024 * 1024:
                messages.error(request, "File size too large. Please upload an image less than 5MB.")
                return redirect('user_dashboard')
                
            # Upload to external service
            image_url = upload_image_to_external_api(profile_picture_file)
            if image_url:
                try:
                    user_profile.profile_picture_url = image_url
                    user_profile.save()
                    messages.success(request, "Profile picture updated successfully!")
                except Exception as e:
                    messages.error(request, f"Error saving profile picture: {str(e)}")
            else:
                messages.error(request, "Failed to upload profile picture. Please try again.")
            return redirect('user_dashboard')
            
        elif 'update_profile' in request.POST:
            profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile, user=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Your profile details have been updated successfully!")
                return redirect('user_dashboard')
            else:
                for field, errors in profile_form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                        
        elif 'update_account' in request.POST:
            account_form = AccountSettingsForm(request.POST, instance=user)
            if account_form.is_valid():
                account_form.save()
                messages.success(request, "Account settings updated successfully!")
                return redirect('user_dashboard')
            else:
                for field, errors in account_form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")

    # Initialize forms for GET request or if POST was invalid
    profile_form = UserProfileForm(instance=user_profile, user=user)
    account_form = AccountSettingsForm(instance=user)

    # --- Fetch History Summary and Stats ---
    recent_history = UserAttempt.objects.filter(user=user).order_by('-attempted_at')[:5]
    for item in recent_history:
        item.action_description = f"Attempted Q{item.question.id} ({item.question.test.name})"

    # Calculate Mock Test / Activity Stats
    total_mocks_attempted = UserAttempt.objects.filter(user=user).values('question__test').distinct().count()
    all_user_attempts = UserAttempt.objects.filter(user=user)
    total_correct_answers = all_user_attempts.filter(is_correct=True).count()
    total_questions_attempted_overall = all_user_attempts.count()

    # Calculate average score
    average_score = 0
    if total_questions_attempted_overall > 0:
        average_score = round((total_correct_answers / total_questions_attempted_overall) * 100, 2)

    # Calculate completion percentage
    # You can customize this calculation based on your specific requirements
    completion_percentage = calculate_completion_percentage(user)

    context = {
        'form': profile_form,
        'account_form': account_form,
        'user': user,
        'recent_history': recent_history,
        'total_mocks_attempted': total_mocks_attempted,
        'average_score': average_score,
        'completion_percentage': completion_percentage,
        'is_mobile': request.user_agent.is_mobile,
    }
    
    return render(request, 'User/dashboard.html', context)

@login_required(login_url='/login/')
def question_partial_view(request, test_id, q_index=0):
    """
    Handles fetching and submitting individual questions via HTMX.
    This view returns only the 'question_card.html' partial.
    """
    test = get_object_or_404(Test, id=test_id)
    subject = test.subject
    questions = list(test.questions.all().order_by('id'))

    # Check if q_index is out of bounds (test finished or invalid index)
    if q_index >= len(questions) or q_index < 0:
        # If test is finished, HTMX will redirect to result page.
        # If invalid index, redirect to dashboard or an error page.
        # For HTMX, we can return an empty response or a redirect header.
        response = HttpResponse(status=204) # 204 No Content
        response['HX-Redirect'] = reverse('display_test_result', args=[test.id])
        return response

    question = questions[q_index]
    submitted = False
    is_correct = None
    selected_option_value = None

    if request.method == 'POST':
        selected_option_value = request.POST.get('option') # HTMX sends form data
        
        # Validate selection
        if selected_option_value is None:
            messages.error(request, "Please select an option before submitting.")
            # Re-render the current question with an error
            # We need to fetch previous attempt data if any
            current_attempt = UserAttempt.objects.filter(user=request.user, question=question).first()
            if current_attempt:
                submitted = True
                is_correct = current_attempt.is_correct
                selected_option_value = current_attempt.selected_option
            return render(request, 'Test_Interface/partials/question_card.html', {
                'test': test,
                'question': question,
                'q_index': q_index,
                'total': len(questions),
                'submitted': submitted,
                'is_correct': is_correct,
                'solution': question.solution,
                'selected': selected_option_value,
                'is_mobile': request.user_agent.is_mobile,
            })

        try:
            selected_option_value = int(selected_option_value)
        except ValueError:
            messages.error(request, "Invalid option selected.")
            current_attempt = UserAttempt.objects.filter(user=request.user, question=question).first()
            if current_attempt:
                submitted = True
                is_correct = current_attempt.is_correct
                selected_option_value = current_attempt.selected_option
            return render(request, 'Test_Interface/partials/question_card.html', {
                'test': test,
                'question': question,
                'q_index': q_index,
                'total': len(questions),
                'submitted': submitted,
                'is_correct': is_correct,
                'solution': question.solution,
                'selected': selected_option_value,
                'is_mobile': request.user_agent.is_mobile,
            })

        is_correct = (selected_option_value == question.correct_option)

        # Create or update UserAttempt
        UserAttempt.objects.update_or_create(
            user=request.user,
            question=question,
            defaults={
                'selected_option': selected_option_value,
                'is_correct': is_correct
            }
        )
        submitted = True # Mark as submitted for immediate feedback display

        if is_correct:
            messages.success(request, "Correct answer!")
        else:
            messages.error(request, f"Incorrect. The correct answer was option {question.correct_option}.")

        # After submission, re-render the same question partial to show feedback
        # HTMX will swap this back into the container
        return render(request, 'Test_Interface/partials/question_card.html', {
            'test': test,
            'question': question,
            'q_index': q_index,
            'total': len(questions),
            'submitted': submitted, # Now True
            'is_correct': is_correct,
            'solution': question.solution,
            'selected': selected_option_value,
            'is_mobile': request.user_agent.is_mobile,
        })

    # GET request: Render the current question partial
    current_attempt = UserAttempt.objects.filter(
        user=request.user,
        question=question
    ).first()

    if current_attempt:
        submitted = True
        is_correct = current_attempt.is_correct
        selected_option_value = current_attempt.selected_option

    return render(request, 'Test_Interface/partials/question_card.html', {
        'test': test,
        'question': question,
        'q_index': q_index,
        'total': len(questions),
        'submitted': submitted,
        'is_correct': is_correct,
        'solution': question.solution,
        'selected': selected_option_value,
        'is_mobile': request.user_agent.is_mobile,
    })

def about_view(request):
    """
    Renders the About Us page with details about the application and its creators.
    """
    # Placeholder data for developers/team members
    team_members = [
        {'name': 'Akash Chaudhari', 'role': 'Lead Developer', 'image_url': 'https://placehold.co/200x200/6366f1/ffffff?text=Akash', 'bio': 'Specializing in backend logic and database design.'},
        {'name': 'Developer Two', 'role': 'Frontend Developer', 'image_url': 'https://placehold.co/200x200/4f46e5/ffffff?text=Dev+Two', 'bio': 'Crafting intuitive user interfaces and experiences.'},
        {'name': 'Developer Three', 'role': 'Content Creator', 'image_url': 'https://placehold.co/200x200/3e35d1/ffffff?text=Dev+Three', 'bio': 'Responsible for curating and adding test content.'},
        {'name': 'Mentor Four', 'role': 'Project Advisor', 'image_url': 'https://placehold.co/200x200/2c24b0/ffffff?text=Mentor', 'bio': 'Providing strategic guidance and quality assurance.'},
    ]
    context = {
        'team_members': team_members,
        'is_mobile': request.user_agent.is_mobile,
    }
    return render(request, 'Test_Interface/about.html', context)

def terms_and_conditions_view(request):
    """
    Renders the Terms and Conditions page.
    """
    context = {
        'is_mobile': request.user_agent.is_mobile,
    }
    return render(request, 'Test_Interface/terms_and_conditions.html', context)

def calculate_average_score(user):
    attempts = UserAttempt.objects.filter(user=user, reviewed=True)
    if not attempts:
        return 0
    total_score = sum(attempt.score for attempt in attempts if attempt.score is not None)
    return round(total_score / attempts.count(), 1)

def calculate_completion_percentage(user):
    attempts = UserAttempt.objects.filter(user=user)
    if not attempts:
        return 0
    completed = attempts.filter(reviewed=True).count()
    return round((completed / attempts.count()) * 100, 1)