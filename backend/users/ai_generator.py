"""
AI Question Generator using Groq (FREE alternative to Gemini)
"""
import logging
from django.conf import settings
import json
import re
from json import JSONDecoder
from .questions import get_all_questions

try:
    from groq import Groq
except Exception:
    Groq = None

logger = logging.getLogger(__name__)


def _get_groq_models():
    configured = (getattr(settings, 'GROQ_MODEL', '') or '').strip()
    default_models = [
        'llama-3.3-70b-versatile',
        'llama-3.1-8b-instant',
    ]
    if configured:
        return [configured, *[m for m in default_models if m != configured]]
    return default_models


def _get_groq_client():
    if Groq is None:
        return None
    api_key = getattr(settings, 'GROQ_API_KEY', '')
    if not api_key:
        return None
    try:
        return Groq(api_key=api_key)
    except Exception:
        logger.exception("Failed to initialize Groq client")
        return None


def _get_static_fallback_questions(topic, difficulty='Easy', num_questions=5):
    questions = [
        q for q in get_all_questions()
        if q.get('topic', '').lower() == topic.lower()
    ]
    if not questions:
        questions = get_all_questions()

    formatted = []
    for index, q in enumerate(questions[:num_questions], start=1):
        formatted.append({
            'id': f"fallback_{topic}_{index}",
            'topic': q.get('topic', topic),
            'difficulty': q.get('difficulty', difficulty),
            'question': q.get('question', ''),
            'options': q.get('options', []),
            'correct_answer': q.get('correct_answer', 0),
            'explanation': q.get('explanation', ''),
            'source': 'Static Fallback',
        })
    return formatted


def _clean_response_text(response_text):
    """Remove markdown fences and normalize common quote variants."""
    cleaned = re.sub(r'```json\s*', '', response_text)
    cleaned = re.sub(r'```\s*', '', cleaned)
    cleaned = cleaned.strip()

    quote_map = {
        '“': '"',
        '”': '"',
        '‘': "'",
        '’': "'",
    }
    for bad, good in quote_map.items():
        cleaned = cleaned.replace(bad, good)

    return cleaned


def _parse_questions_response(response_text):
    """Parse AI response into Python list using tolerant fallbacks."""
    cleaned = _clean_response_text(response_text)

    # Strategy 1: direct parse
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass

    # Strategy 2: parse first JSON value from the first '[' onward
    array_start = cleaned.find('[')
    if array_start != -1:
        decoder = JSONDecoder()
        try:
            parsed, _ = decoder.raw_decode(cleaned[array_start:])
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

    # Strategy 3: extract bracketed payload and remove trailing commas
    first_bracket = cleaned.find('[')
    last_bracket = cleaned.rfind(']')
    if first_bracket != -1 and last_bracket > first_bracket:
        candidate = cleaned[first_bracket:last_bracket + 1]
        candidate = re.sub(r',\s*([}\]])', r'\1', candidate)
        parsed = json.loads(candidate)
        if isinstance(parsed, list):
            return parsed

    raise json.JSONDecodeError('Unable to parse AI response as JSON array', cleaned, 0)


def generate_questions(topic, difficulty='Easy', num_questions=5, allow_fallback=True):
    """
    Generate quiz questions using Groq AI
    
    Args:
        topic: Topic name (e.g., "Logical Reasoning")
        difficulty: Easy, Medium, or Hard
        num_questions: Number of questions to generate
    
    Returns:
        List of question dictionaries
    """
    
    client = _get_groq_client()
    if client is None:
        message = (
            "Groq client unavailable. Ensure GROQ_API_KEY is set and groq package is installed."
        )
        if allow_fallback:
            logger.warning("%s Falling back to static questions.", message)
            return _get_static_fallback_questions(topic, difficulty, num_questions)
        raise RuntimeError(message)

    prompt = f"""Generate {num_questions} multiple-choice questions for a CSE analytics test.

Topic: {topic}
Difficulty: {difficulty}

Requirements:
1. Each question should have exactly 4 options
2. Provide the correct answer as an index (0, 1, 2, or 3)
3. Include a brief explanation
4. Questions should test analytical and problem-solving skills

Return ONLY a valid JSON array in this exact format (no markdown, no extra text):
[
  {{
    "question": "Question text here",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": 0,
    "explanation": "Brief explanation here"
  }}
]"""
    
    last_error = None
    last_response_text = ""

    model_candidates = _get_groq_models()

    for model_name in model_candidates:
        for attempt in range(1, 3):
            try:
                if attempt > 1:
                    logger.info(
                        "Retrying AI generation with model %s (attempt %s/2)",
                        model_name,
                        attempt,
                    )

                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an expert question generator for analytical aptitude tests. "
                                "Respond with valid JSON array only. No markdown, no commentary, "
                                "no trailing commas, and keep all strings properly escaped."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7 if attempt == 1 else 0.2,
                    max_tokens=2600,
                )

                response_text = (response.choices[0].message.content or "").strip()
                last_response_text = response_text

                questions = _parse_questions_response(response_text)

                formatted_questions = []
                for i, q in enumerate(questions[:num_questions]):
                    if not all(key in q for key in ['question', 'options', 'correct_answer', 'explanation']):
                        logger.warning("Skipping invalid question payload")
                        continue

                    options = q.get('options', [])
                    correct_answer = q.get('correct_answer')

                    if not isinstance(options, list) or len(options) != 4:
                        logger.warning("Skipping question with invalid options")
                        continue

                    if not isinstance(correct_answer, int) or correct_answer not in [0, 1, 2, 3]:
                        logger.warning("Skipping question with invalid correct_answer")
                        continue

                    formatted_questions.append({
                        'id': f'ai_{topic}_{i+1}',
                        'topic': topic,
                        'difficulty': difficulty,
                        'question': q['question'],
                        'options': options,
                        'correct_answer': correct_answer,
                        'explanation': q['explanation'],
                        'source': f'Groq AI ({model_name})'
                    })

                if formatted_questions:
                    logger.info("Successfully generated %s questions using Groq model %s", len(formatted_questions), model_name)
                    return formatted_questions

                last_error = ValueError(f"AI returned no valid question objects for model {model_name}")

            except json.JSONDecodeError as e:
                last_error = e
                logger.warning("JSON parse error during AI generation (model=%s attempt=%s/2): %s", model_name, attempt, e)
            except Exception as e:
                last_error = e
                logger.warning("Groq API error during generation (model=%s attempt=%s/2): %s", model_name, attempt, e)

    if isinstance(last_error, json.JSONDecodeError):
        logger.warning("AI response sample after parse failure: %s", (last_response_text or '')[:250])
    else:
        logger.error("Final AI generation failure: %s", last_error)

    if allow_fallback:
        return _get_static_fallback_questions(topic, difficulty, num_questions)

    raise RuntimeError(f"AI generation failed: {last_error or 'unknown error'}")


def generate_adaptive_questions(user, num_questions=5, allow_fallback=True):
    """
    Generate questions based on user's weak areas
    
    Args:
        user: Django User object
        num_questions: Total questions to generate
    
    Returns:
        List of questions targeting weak areas
    """
    from .analytics import get_topic_statistics
    
    # Get weak topics
    topic_stats = get_topic_statistics(user)
    
    if not topic_stats:
        # Default topics if no data
        return generate_questions('Logical Reasoning', 'Easy', num_questions, allow_fallback=allow_fallback)
    
    # Sort by weakness score (highest first)
    weak_topics = [t for t in topic_stats if t['status'] in ['Weak', 'Moderate']]
    
    if not weak_topics:
        # User is strong in all areas, give medium difficulty
        topic = topic_stats[0]['topic']
        return generate_questions(topic, 'Medium', num_questions, allow_fallback=allow_fallback)
    
    # Focus on weakest topic
    weakest_topic = weak_topics[0]
    topic_name = weakest_topic['topic']
    
    # Determine difficulty based on current accuracy
    accuracy = weakest_topic['accuracy']
    if accuracy < 40:
        difficulty = 'Easy'
    elif accuracy < 70:
        difficulty = 'Medium'
    else:
        difficulty = 'Hard'
    
    logger.info("Generating %s %s questions for %s", num_questions, difficulty, topic_name)
    
    return generate_questions(topic_name, difficulty, num_questions, allow_fallback=allow_fallback)