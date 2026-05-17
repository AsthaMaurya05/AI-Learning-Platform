"""
views.py - AI Learning Platform

This module contains all Django view functions for the AI Learning Platform.
It handles user authentication, quiz flow (static and adaptive), analytics 
dashboard, weak area detection, and AI-generated question delivery.

Modules used:
    - analytics.py: For topic statistics and recommendations
    - ai_generator.py: For Groq API question generation
    - questions.py: For static question bank
    - models.py: For data models (PracticeActivity, QuizSession)
"""

from typing import Optional, List, Dict, Any
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST
import random
import json
from .questions import get_all_questions
from .models import PracticeActivity, QuizSession
from .analytics import get_topic_statistics, generate_recommendations


def home(request: HttpRequest) -> HttpResponse:
    """
    Redirect root URL to login page.

    Args:
        request (HttpRequest): The incoming HTTP request object.

    Returns:
        HttpResponseRedirect: Redirects to the login page.

    Notes:
        This is a simple redirect view for the root route ('/').
        Ensures all unauthenticated traffic goes to login.
    """
    return redirect('login')


@require_http_methods(["GET", "POST"])
def login_page(request: HttpRequest) -> HttpResponse:
    """
    Handle user login with safe redirect handling.

    Args:
        request (HttpRequest): The incoming HTTP request object.

    Returns:
        HttpResponse: Rendered login template or redirect to dashboard/next URL.

    Notes:
        - Validates username and password against Django auth system
        - Uses 'next' parameter for safe redirect (prevents open redirect attacks)
        - Redirects already-authenticated users to dashboard
        - Returns error messages on failed login attempt
        - GET request: Shows login form
        - POST request: Authenticates user and logs them in if credentials valid
    """

    next_url = request.POST.get('next') or request.GET.get('next')

    def get_safe_redirect_url():
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return next_url
        return 'dashboard'

    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect(get_safe_redirect_url())
    
    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''

        if not username or not password:
            return render(request, 'login.html', {
                'error': 'Username and password are required.',
                'next': next_url,
            })
        
        # Try to authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Login successful
            login(request, user)
            return redirect(get_safe_redirect_url())

        # Login failed
        return render(request, 'login.html', {
            'error': 'Invalid username or password',
            'next': next_url,
        })
    
    # If GET request, just show the login page
    return render(request, 'login.html', {'next': next_url})


@require_http_methods(["GET", "POST"])
def register_page(request: HttpRequest) -> HttpResponse:
    """
    Handle new user registration with validation.

    Args:
        request (HttpRequest): The incoming HTTP request object.

    Returns:
        HttpResponse: Rendered registration template or redirect to login on success.

    Notes:
        - Validates password strength using Django password validators
        - Ensures passwords match
        - Checks for duplicate username and email (case-insensitive)
        - Creates new user with is_active=True (no email confirmation required)
        - GET request: Shows registration form
        - POST request: Creates user account if all validations pass
        - Redirects to login after successful registration with success message
    """
    
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        email = (request.POST.get('email') or '').strip().lower()
        password = request.POST.get('password') or ''
        password2 = request.POST.get('password2') or ''

        if not username or not email or not password or not password2:
            return render(request, 'register.html', {
                'error': 'All fields are required',
            })
        
        # Validate passwords match
        if password != password2:
            return render(request, 'register.html', {
                'error': 'Passwords do not match'
            })
        
        # Check if username already exists
        if User.objects.filter(username__iexact=username).exists():
            return render(request, 'register.html', {
                'error': 'Username already taken'
            })
        
        # Check if email already exists
        if User.objects.filter(email__iexact=email).exists():
            return render(request, 'register.html', {
                'error': 'Email already registered'
            })

        try:
            validate_password(password, user=User(username=username, email=email))
        except ValidationError as exc:
            return render(request, 'register.html', {
                'error': ' '.join(exc.messages)
            })
        
        User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_active=True,
        )

        messages.success(request, 'Account created successfully. Please log in.')
        return redirect('login')
    
    # If GET request, show registration page
    return render(request, 'register.html')


@login_required(login_url='login')
def dashboard(request: HttpRequest) -> HttpResponse:
    """
    Display user dashboard with practice statistics and analytics charts.

    Args:
        request (HttpRequest): The incoming HTTP request object (must be authenticated).

    Returns:
        HttpResponse: Rendered dashboard template with user statistics and charts.

    Notes:
        - Calculates total questions attempted, overall accuracy, and average time
        - Aggregates topic-wise statistics (accuracy per topic)
        - Identifies weak areas (topics with <60% accuracy)
        - Fetches last 10 quiz sessions for accuracy trend chart
        - Returns empty stats (0s) for new users with no practice data
        - Uses Chart.js JSON format for frontend chart rendering
        - Requires login; redirects to login page if not authenticated
    """
    
    # Get user's practice data
    practice_data = PracticeActivity.objects.filter(user=request.user)
    
    # Calculate statistics
    total_attempted = practice_data.count()
    
    if total_attempted > 0:
        correct_count = practice_data.filter(is_correct=True).count()
        accuracy = (correct_count / total_attempted) * 100
        avg_time = practice_data.aggregate(models.Avg('time_taken'))['time_taken__avg']
        
        # Topic-wise statistics
        from django.db.models import Count, Q
        topic_stats_raw = practice_data.values('topic').annotate(
            total=Count('id'),
            correct=Count('id', filter=Q(is_correct=True))
        )
        
        # Process topic stats
        topic_stats = []
        topic_names = []
        topic_accuracies = []
        weak_topics = []
        
        for topic in topic_stats_raw:
            topic_accuracy = (topic['correct'] / topic['total']) * 100 if topic['total'] > 0 else 0
            
            topic_stats.append({
                'name': topic['topic'],
                'total': topic['total'],
                'correct': topic['correct'],
                'accuracy': topic_accuracy
            })
            
            topic_names.append(topic['topic'])
            topic_accuracies.append(round(topic_accuracy, 1))
            
            if topic_accuracy < 60:
                weak_topics.append(topic['topic'])
        
        weak_area_count = len(weak_topics)
        
        # Get quiz sessions for accuracy trend
        quiz_sessions = QuizSession.objects.filter(user=request.user).order_by('completed_at')[:10]
        
        session_dates = []
        session_accuracies = []
        
        for session in quiz_sessions:
            # Format date as "Jan 15"
            session_dates.append(session.completed_at.strftime('%b %d'))
            session_accuracies.append(round(session.accuracy, 1))
        
        # Get recent sessions for table
        recent_sessions = QuizSession.objects.filter(user=request.user).order_by('-completed_at')[:5]
        
    else:
        accuracy = 0
        avg_time = 0
        weak_area_count = 0
        topic_stats = []
        topic_names = []
        topic_accuracies = []
        session_dates = []
        session_accuracies = []
        recent_sessions = []
    
    context = {
        'total_attempted': total_attempted,
        'accuracy': round(accuracy, 1),
        'avg_time': round(avg_time, 1) if avg_time else 0,
        'weak_area_count': weak_area_count,
        'topic_stats': topic_stats,
        'topic_names': json.dumps(topic_names),
        'topic_accuracies': json.dumps(topic_accuracies),
        'session_dates': json.dumps(session_dates),
        'session_accuracies': json.dumps(session_accuracies),
        'recent_sessions': recent_sessions,
    }
    
    return render(request, 'dashboard.html', context)


@login_required(login_url='login')
def practice_entry(request: HttpRequest) -> HttpResponse:
    """
    Route practice button clicks to appropriate quiz type.

    Args:
        request (HttpRequest): The incoming HTTP request object (must be authenticated).

    Returns:
        HttpResponseRedirect: Redirects to quiz or recommendations page.

    Notes:
        - First-time users (no practice attempts) are sent to static quiz
        - Returning users are sent to recommendations page to see weak areas
        - Requires login; redirects to login page if not authenticated
    """
    has_attempted = PracticeActivity.objects.filter(user=request.user).exists()

    if has_attempted:
        return redirect('recommendations')

    return redirect('quiz')

@login_required(login_url='login')
@require_POST
def logout_user(request: HttpRequest) -> HttpResponse:
    """
    Log out the authenticated user.

    Args:
        request (HttpRequest): The incoming HTTP request object (must be POST and authenticated).

    Returns:
        HttpResponseRedirect: Redirects to login page.

    Notes:
        - Requires POST request (CSRF protected)
        - Requires login; redirects to login page if not authenticated
        - Clears user session after logout
        - Redirects to login page after successful logout
    """
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def quiz(request: HttpRequest) -> HttpResponse:
    """
    Handle static quiz flow with question delivery and answer submission.

    Args:
        request (HttpRequest): The incoming HTTP request object (must be authenticated).

    Returns:
        HttpResponse: Rendered quiz template with current question or redirect to summary.

    Notes:
        - Initializes session with shuffled questions on first request or 'new' parameter
        - Stores quiz state in session: current_question, correct_answers, answers list
        - Shuffles questions per session for variety
        - On POST: Validates answer, saves to database (PracticeActivity), moves to next question
        - After 10 questions: Redirects to quiz_summary
        - Requires login; redirects to login page if not authenticated
        - GET request: Shows current question
        - POST request: Submits answer and loads next question
    """
    
    # Initialize session variables if starting new quiz
    if 'quiz_started' not in request.session or request.GET.get('new'):
        request.session['quiz_started'] = True
        request.session['current_question'] = 1
        request.session['correct_answers'] = 0
        request.session['answers'] = []
        
        # SHUFFLE questions for this session
        all_questions = get_all_questions()
        shuffled = all_questions.copy()
        random.shuffle(shuffled)
        
        # Store shuffled questions in session
        request.session['session_questions'] = shuffled
        request.session.modified = True
    
    # Get current question number
    current_q_num = request.session.get('current_question', 1)
    
    # Get questions from session (shuffled)
    all_questions = request.session.get('session_questions')
    if not all_questions:
        # Fallback if session lost
        all_questions = get_all_questions()
    
    total_questions = len(all_questions)
    
    # Check if quiz is complete
    if current_q_num > total_questions:
        return redirect('quiz_summary')
    
    # Get current question
    question = all_questions[current_q_num - 1]
    
    # Handle form submission
    submitted = False
    is_correct = False
    
    if request.method == 'POST':
        selected_option = request.POST.get('selected_option')
        time_taken = request.POST.get('time_taken', 0)
        question_id = request.POST.get('question_id')
        
        # Check if answer is correct
        is_correct = int(selected_option) == question['correct_answer']
        
        # Save to database
        PracticeActivity.objects.create(
            user=request.user,
            question_id=int(question_id),
            topic=question['topic'],
            difficulty=question['difficulty'],
            selected_option=int(selected_option),
            correct_answer=question['correct_answer'],
            is_correct=is_correct,
            time_taken=int(time_taken)
        )
        
        # Store answer data in session
        answer_data = {
            'question_id': int(question_id),
            'topic': question['topic'],
            'selected_option': int(selected_option),
            'correct_answer': question['correct_answer'],
            'is_correct': is_correct,
            'time_taken': int(time_taken)
        }
        
        if 'answers' not in request.session:
            request.session['answers'] = []
        
        answers = request.session['answers']
        answers.append(answer_data)
        request.session['answers'] = answers
        
        # Update correct answers count
        if is_correct:
            request.session['correct_answers'] = request.session.get('correct_answers', 0) + 1
        
        # Move to next question
        request.session['current_question'] = current_q_num + 1
        
        submitted = True
        request.session.modified = True
    
    context = {
        'question': question,
        'current_question_num': current_q_num,
        'total_questions': total_questions,
        'submitted': submitted,
        'is_correct': is_correct,
    }
    
    return render(request, 'quiz.html', context)

@login_required(login_url='login')
def quiz_summary(request: HttpRequest) -> HttpResponse:
    """
    Display quiz results summary after completion.

    Args:
        request (HttpRequest): The incoming HTTP request object (must be authenticated).

    Returns:
        HttpResponse: Rendered quiz summary template with statistics.

    Notes:
        - Retrieves quiz data from session (answers, correct count)
        - Calculates total time, average time per question, and accuracy
        - Saves QuizSession to database for analytics (only if answers exist)
        - Clears session data for next quiz
        - Requires login; redirects to login page if not authenticated
    """
    
    # Get quiz data from session
    answers = request.session.get('answers', [])
    correct_answers = request.session.get('correct_answers', 0)
    total_questions = len(get_all_questions())
    
    # Calculate statistics
    total_time = sum(answer['time_taken'] for answer in answers)
    avg_time = total_time / total_questions if total_questions > 0 else 0
    accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    
    # Save quiz session to database
    if answers:  # Only save if there were actual answers
        QuizSession.objects.create(
            user=request.user,
            total_questions=total_questions,
            correct_answers=correct_answers,
            accuracy=accuracy,
            total_time=total_time
        )
    
    # Clear session data for next quiz
    request.session['quiz_started'] = False
    request.session['current_question'] = 1
    request.session['correct_answers'] = 0
    request.session['answers'] = []
    request.session.modified = True
    
    context = {
        'correct_answers': correct_answers,
        'total_questions': total_questions,
        'accuracy': accuracy,
        'total_time': total_time,
        'avg_time': avg_time,
    }
    
    return render(request, 'quiz_summary.html', context)


@login_required(login_url='login')
def weak_areas(request: HttpRequest) -> HttpResponse:
    """
    Display weak area analysis with topic-wise performance insights.

    Args:
        request (HttpRequest): The incoming HTTP request object (must be authenticated).

    Returns:
        HttpResponse: Rendered weak areas template with analytics and recommendations.

    Notes:
        - Calls analytics.get_topic_statistics() to calculate per-topic performance
        - Calls analytics.generate_recommendations() to create personalized suggestions
        - Topics are sorted by weakness score (highest weakness first)
        - Classifies topics as Strong, Moderate, or Weak based on accuracy and consistency
        - Requires login; redirects to login page if not authenticated
    """
    
    topic_analysis = get_topic_statistics(request.user)
    recommendations = generate_recommendations(topic_analysis)
    
    context = {
        'topic_analysis': topic_analysis,
        'recommendations': recommendations
    }
    
    return render(request, 'weak_areas.html', context)

@login_required(login_url='login')
def recommendations_page(request: HttpRequest) -> HttpResponse:
    """
    Display personalized practice recommendations based on user performance.

    Args:
        request (HttpRequest): The incoming HTTP request object (must be authenticated).

    Returns:
        HttpResponse: Rendered recommendations template with prioritized suggestions.

    Notes:
        - Calls analytics.get_topic_statistics() to analyze topic performance
        - Calls analytics.generate_recommendations() to create prioritized recommendations
        - Recommendations are grouped: high_priority, medium_priority, maintain
        - Each recommendation includes topic, reason (why this topic), and suggestion
        - Requires login; redirects to login page if not authenticated
    """
    
    topic_analysis = get_topic_statistics(request.user)
    recommendations = generate_recommendations(topic_analysis)
    
    context = {
        'recommendations': recommendations,
    }
    
    return render(request, 'recommendations.html', context)
@login_required(login_url='login')
def adaptive_quiz(request: HttpRequest) -> HttpResponse:
    """
    Handle adaptive AI-generated quiz flow based on user's weak areas.

    Args:
        request (HttpRequest): The incoming HTTP request object (must be authenticated).
        Optional GET parameters:
            - topic (str): Specific topic to generate questions for (overrides weak area detection)
            - new (bool): Force new quiz generation (overrides cached questions)

    Returns:
        HttpResponse: Rendered quiz template with AI-generated question or error page if generation fails.

    Notes:
        - Generates questions using Groq API via ai_generator.generate_adaptive_questions()
        - If topic param provided: Generates for that specific topic only
        - If topic param absent: Generates for user's weakest area (if data exists)
        - Questions are cached in session; new questions only if 'new' param or topic changes
        - On API failure: Shows error page with Groq API configuration instructions
        - On POST: Validates answer (must be 0-3), saves to database, moves to next question
        - After all questions: Redirects to adaptive_quiz_summary
        - Requires login; redirects to login page if not authenticated
    """
    
    # Get topic from URL parameter
    topic_param = request.GET.get('topic', None)
    
    # ALWAYS start fresh for adaptive quiz OR if 'new' parameter exists
    force_new = request.GET.get('new') or request.GET.get('topic')
    
    if 'adaptive_quiz_started' not in request.session or force_new:
        # Clear ALL adaptive quiz session data
        request.session.pop('adaptive_quiz_started', None)
        request.session.pop('adaptive_current_question', None)
        request.session.pop('adaptive_questions', None)
        request.session.pop('adaptive_correct', None)
        request.session.pop('adaptive_answers', None)
        
        # Initialize fresh session
        request.session['adaptive_quiz_started'] = True
        request.session['adaptive_current_question'] = 0
        request.session['adaptive_correct'] = 0
        request.session['adaptive_answers'] = []
        request.session.modified = True
    
    # ALWAYS generate fresh questions if we don't have any OR if topic changed
    current_questions = request.session.get('adaptive_questions')
    if not current_questions or force_new:
        questions = None
        error_message = None
        
        try:
            if topic_param:
                # Generate for specific topic
                from .ai_generator import generate_questions
                questions = generate_questions(topic_param, 'Easy', 5, allow_fallback=False)
            else:
                # Generate based on weak areas
                from .ai_generator import generate_adaptive_questions
                questions = generate_adaptive_questions(request.user, 5, allow_fallback=False)
            
            # Validate questions
            if questions and len(questions) > 0:
                # Store in session
                request.session['adaptive_questions'] = questions
                request.session['adaptive_current_question'] = 0  # Reset to first question
                request.session.modified = True
                
            else:
                error_message = "AI returned empty question list"
        
        except Exception as e:
            error_message = str(e)
        
        # If AI failed, show error page
        if not questions or len(questions) == 0:
            return render(request, 'quiz_error.html', {
                'error': (
                    f'Failed to generate AI questions. Error: {error_message or "Unknown error"}. '
                    'Please configure a valid GROQ_API_KEY and retry.'
                )
            })
    
    # Get questions from session
    questions = request.session.get('adaptive_questions')
    current_index = request.session.get('adaptive_current_question', 0)
    
    # Check if quiz is complete
    if current_index >= len(questions):
        return redirect('adaptive_quiz_summary')
    
    current_question = questions[current_index]
    
    # Handle answer submission
    submitted = False
    is_correct = False
    
    if request.method == 'POST':
        selected_option = int(request.POST.get('selected_option'))
        time_taken = int(request.POST.get('time_taken', 0))
        
        is_correct = selected_option == current_question['correct_answer']
        
        # Save to database
        PracticeActivity.objects.create(
            user=request.user,
            question_id=abs(hash(str(current_question.get('id', f'ai_{current_index}')))),
            topic=current_question['topic'],
            difficulty=current_question.get('difficulty', 'Easy'),
            selected_option=selected_option,
            correct_answer=current_question['correct_answer'],
            is_correct=is_correct,
            time_taken=time_taken
        )
        
        # Update session
        if is_correct:
            request.session['adaptive_correct'] = request.session.get('adaptive_correct', 0) + 1
        
        request.session['adaptive_current_question'] = current_index + 1
        request.session.modified = True
        
        submitted = True
    
    context = {
        'question': current_question,
        'current_question_num': current_index + 1,
        'total_questions': len(questions),
        'submitted': submitted,
        'is_correct': is_correct,
        'is_adaptive': True,
    }
    
    return render(request, 'quiz.html', context)



@login_required(login_url='login')
def adaptive_quiz_summary(request: HttpRequest) -> HttpResponse:
    """
    Display results summary for adaptive AI-generated quiz.

    Args:
        request (HttpRequest): The incoming HTTP request object (must be authenticated).

    Returns:
        HttpResponse: Rendered quiz summary template with adaptive quiz statistics.

    Notes:
        - Retrieves adaptive quiz data from session
        - Calculates accuracy from correct count and total questions
        - Clears adaptive quiz session data for next adaptive quiz
        - Uses same summary template as static quiz (quiz_summary.html)
        - Sets is_adaptive flag for frontend template differentiation
        - Requires login; redirects to login page if not authenticated
    """
    
    questions = request.session.get('adaptive_questions', [])
    correct = request.session.get('adaptive_correct', 0)
    total = len(questions)
    
    accuracy = (correct / total * 100) if total > 0 else 0
    
    # Clear session
    request.session['adaptive_quiz_started'] = False
    request.session['adaptive_questions'] = None
    request.session['adaptive_current_question'] = 0
    request.session['adaptive_correct'] = 0
    request.session.modified = True
    
    context = {
        'correct_answers': correct,
        'total_questions': total,
        'accuracy': accuracy,
        'total_time': 0,
        'avg_time': 0,
        'is_adaptive': True,
    }
    
    return render(request, 'quiz_summary.html', context)