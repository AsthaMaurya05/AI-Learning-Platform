from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.contrib import messages
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST
from datetime import timedelta
import random
from .questions import get_all_questions, get_question_by_id
from .models import PracticeActivity, QuizSession


REGISTRATION_OTP_SESSION_KEY = 'registration_otp'


def _clear_registration_otp(request):
    request.session.pop(REGISTRATION_OTP_SESSION_KEY, None)
    request.session.modified = True


def _store_and_send_registration_otp(request, user):
    otp = f"{random.randint(0, 999999):06d}"
    request.session[REGISTRATION_OTP_SESSION_KEY] = {
        'user_id': user.id,
        'otp': otp,
        'expires_at': (timezone.now() + timedelta(minutes=10)).isoformat(),
        'attempts': 0,
    }
    request.session.modified = True

    send_mail(
        subject='Your OTP for AI Learning Platform',
        message=(
            f'Hi {user.username},\n\n'
            f'Your OTP is: {otp}\n'
            'This OTP is valid for 10 minutes.\n\n'
            'If you did not request this, you can ignore this email.'
        ),
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
        recipient_list=[user.email],
        fail_silently=False,
    )

def home(request):
    """Redirect root route to login flow"""
    return redirect('login')


@require_http_methods(["GET", "POST"])
def login_page(request):
    """Handle user login"""

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
        else:
            existing_user = User.objects.filter(username__iexact=username).first()
            if existing_user and not existing_user.is_active and existing_user.check_password(password):
                try:
                    _store_and_send_registration_otp(request, existing_user)
                    messages.info(request, 'Account not verified. OTP sent to your email.')
                    return redirect('verify_email_otp')
                except Exception:
                    return render(request, 'login.html', {
                        'error': 'Account is not verified and OTP could not be sent. Please try again.',
                        'next': next_url,
                    })

            # Login failed
            return render(request, 'login.html', {
                'error': 'Invalid username or password',
                'next': next_url,
            })
    
    # If GET request, just show the login page
    return render(request, 'login.html', {'next': next_url})


@require_http_methods(["GET", "POST"])
def register_page(request):
    """Handle user registration"""
    
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
        
        # Create new user as inactive until OTP verification
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_active=False,
        )

        try:
            _store_and_send_registration_otp(request, user)
        except Exception:
            user.delete()
            return render(request, 'register.html', {
                'error': 'Could not send OTP email. Please try again.',
            })

        messages.success(request, 'Account created. OTP sent to your email. Please verify to continue.')
        return redirect('verify_email_otp')
    
    # If GET request, show registration page
    return render(request, 'register.html')


@require_http_methods(["GET", "POST"])
def verify_email_otp(request):
    otp_data = request.session.get(REGISTRATION_OTP_SESSION_KEY)

    if not otp_data:
        messages.error(request, 'No OTP session found. Please register again.')
        return redirect('register')

    try:
        user = User.objects.get(pk=otp_data.get('user_id'))
    except User.DoesNotExist:
        _clear_registration_otp(request)
        messages.error(request, 'Verification session expired. Please register again.')
        return redirect('register')

    if request.method == 'POST':
        entered_otp = (request.POST.get('otp') or '').strip()
        expires_at = parse_datetime(otp_data.get('expires_at', ''))

        if not expires_at or timezone.now() > expires_at:
            return render(request, 'verify_otp.html', {
                'email': user.email,
                'error': 'OTP expired. Please request a new OTP.',
            })

        attempts = int(otp_data.get('attempts', 0)) + 1
        otp_data['attempts'] = attempts
        request.session[REGISTRATION_OTP_SESSION_KEY] = otp_data
        request.session.modified = True

        if attempts > 5:
            return render(request, 'verify_otp.html', {
                'email': user.email,
                'error': 'Too many attempts. Please request a new OTP.',
            })

        if entered_otp == otp_data.get('otp'):
            user.is_active = True
            user.save(update_fields=['is_active'])
            _clear_registration_otp(request)
            messages.success(request, 'Email verified successfully! Please log in.')
            return redirect('login')

        return render(request, 'verify_otp.html', {
            'email': user.email,
            'error': 'Invalid OTP. Please try again.',
        })

    return render(request, 'verify_otp.html', {
        'email': user.email,
    })


@require_POST
def resend_email_otp(request):
    otp_data = request.session.get(REGISTRATION_OTP_SESSION_KEY)
    if not otp_data:
        messages.error(request, 'No verification session found. Please register again.')
        return redirect('register')

    try:
        user = User.objects.get(pk=otp_data.get('user_id'))
    except User.DoesNotExist:
        _clear_registration_otp(request)
        messages.error(request, 'Verification session expired. Please register again.')
        return redirect('register')

    if user.is_active:
        _clear_registration_otp(request)
        messages.success(request, 'Account already verified. Please log in.')
        return redirect('login')

    try:
        _store_and_send_registration_otp(request, user)
    except Exception:
        messages.error(request, 'Could not resend OTP right now. Please try again.')
        return redirect('verify_email_otp')

    messages.success(request, 'New OTP sent to your email.')
    return redirect('verify_email_otp')


@login_required(login_url='login')
def dashboard(request):
    """Display user dashboard with real statistics and charts"""
    
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
    
    import json
    
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
def practice_entry(request):
    """Route practice clicks: first-time users get static quiz, returning users get recommendations."""
    has_attempted = PracticeActivity.objects.filter(user=request.user).exists()

    if has_attempted:
        return redirect('recommendations')

    return redirect('quiz')

@login_required(login_url='login')
@require_POST
def logout_user(request):
    """Handle user logout"""
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def quiz(request):
    """Handle quiz questions and answers"""
    
    # Initialize session variables if starting new quiz
    if 'quiz_started' not in request.session or request.GET.get('new'):
        print("Starting new regular quiz session")  # DEBUG
        request.session['quiz_started'] = True
        request.session['current_question'] = 1
        request.session['correct_answers'] = 0
        request.session['answers'] = []
        
        # SHUFFLE questions for this session
        from .questions import get_all_questions
        import random
        
        all_questions = get_all_questions()
        shuffled = all_questions.copy()
        random.shuffle(shuffled)
        
        # Store shuffled questions in session
        request.session['session_questions'] = shuffled
        request.session.modified = True
        print(f"Shuffled {len(shuffled)} questions for this session")  # DEBUG
    
    # Get current question number
    current_q_num = request.session.get('current_question', 1)
    
    # Get questions from session (shuffled)
    all_questions = request.session.get('session_questions')
    if not all_questions:
        # Fallback if session lost
        from .questions import get_all_questions
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
def quiz_summary(request):
    """Display quiz results summary"""
    
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


from .analytics import get_topic_statistics, generate_recommendations

@login_required(login_url='login')
def weak_areas(request):
    """Display weak area analysis with ML-based insights"""
    
    topic_analysis = get_topic_statistics(request.user)
    recommendations = generate_recommendations(topic_analysis)
    
    context = {
        'topic_analysis': topic_analysis,
        'recommendations': recommendations
    }
    
    return render(request, 'weak_areas.html', context)




from .ai_generator import generate_adaptive_questions
from .analytics import get_topic_statistics, generate_recommendations

@login_required(login_url='login')
def recommendations_page(request):
    """Display personalized recommendations"""
    
    topic_analysis = get_topic_statistics(request.user)
    recommendations = generate_recommendations(topic_analysis)
    
    context = {
        'recommendations': recommendations,
    }
    
    return render(request, 'recommendations.html', context)
@login_required(login_url='login')
def adaptive_quiz(request):
    """
    Adaptive quiz - ONLY uses AI-generated questions
    Forces fresh generation every time
    """
    
    # Get topic from URL parameter
    topic_param = request.GET.get('topic', None)
    
    # ALWAYS start fresh for adaptive quiz OR if 'new' parameter exists
    force_new = request.GET.get('new') or request.GET.get('topic')
    
    if 'adaptive_quiz_started' not in request.session or force_new:
        print("\n" + "=" * 70)
        print("STARTING FRESH ADAPTIVE QUIZ SESSION")
        print("=" * 70)
        
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
        
        print("Session cleared and reset")
    
    # ALWAYS generate fresh questions if we don't have any OR if topic changed
    current_questions = request.session.get('adaptive_questions')
    if not current_questions or force_new:
        print("\nGenerating new AI questions...")
        print(f"Topic requested: {topic_param if topic_param else 'Auto (weak areas)'}")
        
        questions = None
        error_message = None
        
        try:
            if topic_param:
                # Generate for specific topic
                print(f"Mode: Specific Topic - '{topic_param}'")
                from .ai_generator import generate_questions
                questions = generate_questions(topic_param, 'Easy', 5)
            else:
                # Generate based on weak areas
                print("Mode: Adaptive (analyzing weak areas)")
                from .ai_generator import generate_adaptive_questions
                questions = generate_adaptive_questions(request.user, 5)
            
            # Validate questions
            if questions and len(questions) > 0:
                print("AI generation success")
                print(f"   - Generated: {len(questions)} questions")
                print(f"   - Source: {questions[0].get('source', 'Unknown')}")
                print(f"   - First topic: {questions[0].get('topic', 'Unknown')}")
                
                # Store in session
                request.session['adaptive_questions'] = questions
                request.session['adaptive_current_question'] = 0  # Reset to first question
                request.session.modified = True
                
            else:
                error_message = "AI returned empty question list"
                print(f"Error: {error_message}")
        
        except Exception as e:
            error_message = str(e)
            print(f"AI generation error: {error_message}")
            import traceback
            traceback.print_exc()
        
        # If AI failed, show error page
        if not questions or len(questions) == 0:
            print("\nStopping - Cannot proceed without AI questions")
            return render(request, 'quiz_error.html', {
                'error': f'Failed to generate AI questions. Error: {error_message or "Unknown error"}. Please check terminal logs.'
            })
    
    # Get questions from session
    questions = request.session.get('adaptive_questions')
    current_index = request.session.get('adaptive_current_question', 0)
    
    print(f"\nDisplaying: Question {current_index + 1}/{len(questions)}")
    
    # Check if quiz is complete
    if current_index >= len(questions):
        print("Quiz complete. Redirecting to summary...\n")
        return redirect('adaptive_quiz_summary')
    
    current_question = questions[current_index]
    print(f"   Source: {current_question.get('source', 'Unknown')}")
    print(f"   Topic: {current_question.get('topic', 'Unknown')}")
    print(f"   ID: {current_question.get('id', 'Unknown')}")
    
    # Handle answer submission
    submitted = False
    is_correct = False
    
    if request.method == 'POST':
        print("\nProcessing answer submission...")
        selected_option = int(request.POST.get('selected_option'))
        time_taken = int(request.POST.get('time_taken', 0))
        
        is_correct = selected_option == current_question['correct_answer']
        print(f"   Answer: {'Correct' if is_correct else 'Wrong'}")
        
        # Save to database
        try:
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
            print("   Saved to database")
        except Exception as e:
            print(f"   Database error: {e}")
        
        # Update session
        if is_correct:
            request.session['adaptive_correct'] = request.session.get('adaptive_correct', 0) + 1
        
        request.session['adaptive_current_question'] = current_index + 1
        request.session.modified = True
        
        submitted = True
        print("   Session updated\n")
    
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
def adaptive_quiz_summary(request):
    """Show summary for adaptive quiz"""
    
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
        'total_time': 0,  # Can add timer later
        'avg_time': 0,
        'is_adaptive': True,
    }
    
    return render(request, 'quiz_summary.html', context)