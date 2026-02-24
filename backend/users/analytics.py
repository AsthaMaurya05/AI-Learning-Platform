"""
Analytics module for detecting weak areas and generating recommendations
"""
from django.db.models import Count, Q, Avg
from .models import PracticeActivity
import statistics


def calculate_weakness_score(accuracy, avg_time, consistency):
    """
    Calculate weakness score (0-1)
    0 = Strong, 1 = Very Weak
    
    Factors:
    - Low accuracy = higher weakness
    - High time = higher weakness (struggling)
    - Low consistency = higher weakness (not improving)  
    """
    
    # Normalize accuracy (invert: low accuracy = high weakness)
    accuracy_weakness = (100 - accuracy) / 100
    
    # Normalize time (if avg_time > 60s, that's weak)
    time_weakness = min(avg_time / 120, 1.0)  # Cap at 120s
    
    # Consistency weakness (if consistency < 50%, that's weak)
    consistency_weakness = (100 - consistency) / 100
    
    # Weighted average
    weakness_score = (
        accuracy_weakness * 0.5 +      # Accuracy is most important
        time_weakness * 0.3 +           # Time matters
        consistency_weakness * 0.2      # Consistency matters less
    )
    
    return round(weakness_score, 2)


def get_topic_statistics(user):
    """
    Get detailed statistics for each topic
    Returns list of topics with their weakness scores
    """
    
    practice_data = PracticeActivity.objects.filter(user=user)
    
    if not practice_data.exists():
        return []
    
    # Group by topic
    topic_stats_raw = practice_data.values('topic').annotate(
        total=Count('id'),
        correct=Count('id', filter=Q(is_correct=True)),
        avg_time=Avg('time_taken')
    )
    
    topic_analysis = []
    
    for topic in topic_stats_raw:
        topic_name = topic['topic']
        total = topic['total']
        correct = topic['correct']
        avg_time = topic['avg_time']
        
        # Calculate accuracy
        accuracy = (correct / total * 100) if total > 0 else 0
        
        # Calculate consistency (how stable is performance over time)
        # Get last 5 attempts for this topic
        recent_attempts = practice_data.filter(topic=topic_name).order_by('-attempted_at')[:5]
        recent_accuracies = [1 if attempt.is_correct else 0 for attempt in recent_attempts]
        
        if len(recent_accuracies) > 1:
            # Calculate standard deviation (lower = more consistent)
            std_dev = statistics.stdev(recent_accuracies) if len(recent_accuracies) > 1 else 0
            consistency = max(0, 100 - (std_dev * 100))
        else:
            consistency = 50  # Default for insufficient data
        
        # Calculate weakness score
        weakness_score = calculate_weakness_score(accuracy, avg_time, consistency)
        
        # Determine status
        if weakness_score < 0.3:
            status = 'Strong'
            status_emoji = ''
            priority = 'Low'
        elif weakness_score < 0.6:
            status = 'Moderate'
            status_emoji = ''
            priority = 'Medium'
        else:
            status = 'Weak'
            status_emoji = ''
            priority = 'High'
        
        topic_analysis.append({
            'topic': topic_name,
            'total_attempts': total,
            'correct_answers': correct,
            'accuracy': round(accuracy, 1),
            'avg_time': round(avg_time, 1),
            'consistency': round(consistency, 1),
            'weakness_score': weakness_score,
            'status': status,
            'status_emoji': status_emoji,
            'priority': priority
        })
    
    # Sort by weakness score (highest first)
    topic_analysis.sort(key=lambda x: x['weakness_score'], reverse=True)
    
    return topic_analysis


def generate_recommendations(topic_analysis):
    """
    Generate personalized practice recommendations
    """
    
    if not topic_analysis:
        return {
            'high_priority': [],
            'medium_priority': [],
            'maintain': [],
            'message': 'Start practicing to get personalized recommendations!'
        }
    
    high_priority = []
    medium_priority = []
    maintain = []
    
    for topic in topic_analysis:
        recommendation = {
            'topic': topic['topic'],
            'reason': '',
            'suggestion': ''
        }
        
        if topic['priority'] == 'High':
            if topic['accuracy'] < 40:
                recommendation['reason'] = f"Very low accuracy ({topic['accuracy']}%)"
                recommendation['suggestion'] = f"Start with easy {topic['topic']} questions and focus on understanding concepts"
            elif topic['avg_time'] > 90:
                recommendation['reason'] = f"Taking too long (avg {topic['avg_time']}s)"
                recommendation['suggestion'] = f"Practice speed-solving {topic['topic']} questions with a timer"
            else:
                recommendation['reason'] = f"Inconsistent performance"
                recommendation['suggestion'] = f"Practice {topic['topic']} regularly to build consistency"
            
            high_priority.append(recommendation)
        
        elif topic['priority'] == 'Medium':
            recommendation['reason'] = f"Moderate accuracy ({topic['accuracy']}%)"
            recommendation['suggestion'] = f"Practice medium-level {topic['topic']} questions"
            medium_priority.append(recommendation)
        
        else:  # Low priority / Strong
            recommendation['reason'] = f"Strong performance ({topic['accuracy']}%)"
            recommendation['suggestion'] = f"Maintain with occasional {topic['topic']} practice"
            maintain.append(recommendation)
    
    # Generate summary message
    if high_priority:
        message = f"Focus on {len(high_priority)} weak area(s) to improve quickly!"
    elif medium_priority:
        message = "Good progress! Work on moderate areas to reach excellence."
    else:
        message = "Excellent! You're strong in all areas. Keep practicing!"
    
    return {
        'high_priority': high_priority,
        'medium_priority': medium_priority,
        'maintain': maintain,
        'message': message
    }