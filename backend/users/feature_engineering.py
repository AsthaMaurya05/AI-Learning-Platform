"""
Feature Engineering for ML Models
Extracts features from practice data for machine learning
"""
import numpy as np
from .models import PracticeActivity
from django.db.models import Count, Q, Avg


def extract_topic_features(user, topic_name):
    """
    Extract features for a specific topic
    Returns feature vector for ML models
    """
    
    practice_data = PracticeActivity.objects.filter(
        user=user, 
        topic=topic_name
    ).order_by('attempted_at')
    
    if not practice_data.exists():
        return None
    
    # Feature 1: Total attempts
    total_attempts = practice_data.count()
    
    # Feature 2: Accuracy
    correct = practice_data.filter(is_correct=True).count()
    accuracy = (correct / total_attempts * 100) if total_attempts > 0 else 0
    
    # Feature 3: Average time taken
    avg_time = practice_data.aggregate(Avg('time_taken'))['time_taken__avg'] or 0
    
    # Feature 4: Recent trend (last 5 attempts)
    recent = list(practice_data.order_by('-attempted_at')[:5])
    if len(recent) >= 2:
        recent_accuracy = sum(1 for q in recent if q.is_correct) / len(recent) * 100
        # Trend: positive if recent > overall
        trend = recent_accuracy - accuracy
    else:
        trend = 0
    
    # Feature 5: Time improvement (are they getting faster?)
    if total_attempts >= 3:
        first_half_avg = practice_data[:total_attempts//2].aggregate(Avg('time_taken'))['time_taken__avg'] or 0
        second_half_avg = practice_data[total_attempts//2:].aggregate(Avg('time_taken'))['time_taken__avg'] or 0
        time_improvement = first_half_avg - second_half_avg
    else:
        time_improvement = 0
    
    # Feature 6: Consistency (standard deviation of results)
    results = [1 if q.is_correct else 0 for q in practice_data]
    consistency = np.std(results) if len(results) > 1 else 0
    
    features = {
        'total_attempts': total_attempts,
        'accuracy': accuracy,
        'avg_time': avg_time,
        'trend': trend,
        'time_improvement': time_improvement,
        'consistency': consistency,
        'topic': topic_name
    }
    
    return features


def get_all_topic_features(user):
    """
    Get features for all topics user has practiced
    """
    
    topics = PracticeActivity.objects.filter(user=user).values_list('topic', flat=True).distinct()
    
    all_features = []
    for topic in topics:
        features = extract_topic_features(user, topic)
        if features:
            all_features.append(features)
    
    return all_features