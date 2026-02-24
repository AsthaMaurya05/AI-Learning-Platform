from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class PracticeActivity(models.Model):
    """
    Store every question attempt by users
    This data will be used for analytics and ML later
    """
    
    # Link to the user who attempted this question
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Question details
    question_id = models.IntegerField()
    topic = models.CharField(max_length=100)
    difficulty = models.CharField(max_length=20, default='Easy')
    
    # User's answer
    selected_option = models.IntegerField()
    correct_answer = models.IntegerField()
    is_correct = models.BooleanField()
    
    # Time tracking
    time_taken = models.IntegerField(help_text="Time taken in seconds")
    attempted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Practice Activity"
        verbose_name_plural = "Practice Activities"
        ordering = ['-attempted_at']  # Most recent first
    
    def __str__(self):
        result = 'Correct' if self.is_correct else 'Wrong'
        return f"{self.user.username} - Q{self.question_id} - {result}"


class QuizSession(models.Model):
    """
    Store complete quiz sessions (10 questions)
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Quiz statistics
    total_questions = models.IntegerField()
    correct_answers = models.IntegerField()
    accuracy = models.FloatField()
    total_time = models.IntegerField(help_text="Total time in seconds")
    
    # Timestamp
    completed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Quiz Session"
        verbose_name_plural = "Quiz Sessions"
        ordering = ['-completed_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.accuracy}% - {self.completed_at.strftime('%Y-%m-%d')}"