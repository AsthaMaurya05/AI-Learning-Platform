from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_page, name='login'),
    path('register/', views.register_page, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_user, name='logout'),
    path('practice/', views.practice_entry, name='practice'),
    path('quiz/', views.quiz, name='quiz'),
    path('quiz/summary/', views.quiz_summary, name='quiz_summary'),
    path('weak-areas/', views.weak_areas, name='weak_areas'),
    path('recommendations/', views.recommendations_page, name='recommendations'),
    path('adaptive-quiz/', views.adaptive_quiz, name='adaptive_quiz'),
    path('adaptive-quiz/summary/', views.adaptive_quiz_summary, name='adaptive_quiz_summary'),
]
