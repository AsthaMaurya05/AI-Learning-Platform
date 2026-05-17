# 🎓 AI Learning Platform - Workflow & Technology Presentation

---

## 📊 EXECUTIVE OVERVIEW

**AI Learning Platform** is an intelligent, adaptive learning system that helps students prepare for competitive exams through AI-powered personalized feedback and weak area detection.

**Key Promise:** Transform scattered quiz attempts into actionable insights with machine learning-driven recommendations.

---

## 🏗️ SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER BROWSER                             │
│                   (HTML5, CSS3, JavaScript)                     │
└────────────────┬────────────────────────────────────────────────┘
                 │ HTTP Requests
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DJANGO WEB SERVER                            │
│  ├─ Authentication & Session Management                         │
│  ├─ View Layer (13 endpoints)                                   │
│  └─ Template Rendering (HTML)                                   │
└────────────────┬────────────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
   ┌─────────┐      ┌──────────────┐
   │ SQLITE3 │      │ GROQ API     │
   │ DATABASE│      │ (LLM Model)  │
   └─────────┘      └──────────────┘
```

---

## 🔄 USER JOURNEY WORKFLOW

### **PHASE 1: AUTHENTICATION**
```
User Opens Website
        ↓
┌─────────────────────────────────────────┐
│  [1] Login/Register Page                │
├─────────────────────────────────────────┤
│  Technology: Django Auth Framework      │
│  Backend: authenticate() & User Model   │
│  Database: User table in SQLite3        │
│  Security: Django password hashing      │
└─────────────────────────────────────────┘
        ↓
   [✓] Account Created/Verified
        ↓
   Redirect to Dashboard
```

**Tech Used:**
- **Django Auth System**: Built-in user authentication
- **Password Validation**: Checks for strength & duplication
- **Session Management**: Django middleware for session tracking
- **Database**: SQLite3 User table

---

### **PHASE 2: DASHBOARD & ANALYTICS**
```
User Lands on Dashboard
        ↓
┌─────────────────────────────────────────────────────────────┐
│  [2] Analytics Dashboard                                    │
├─────────────────────────────────────────────────────────────┤
│  Display Real-time Statistics:                              │
│  ├─ Overall Accuracy (%)                                    │
│  ├─ Total Quizzes Attempted                                 │
│  ├─ Average Time Per Question (seconds)                     │
│  ├─ Performance Trends (Chart.js visualization)             │
│  └─ Topic-wise Breakdown                                    │
└─────────────────────────────────────────────────────────────┘
```

**Tech Used:**
- **Backend**: analytics.py module
  - `get_topic_statistics()`: Aggregates quiz data by topic
  - Calculates: Accuracy, Attempt Count, Time Metrics
  - Uses Django ORM `aggregate()` & `annotate()` functions
  
- **Frontend**: Chart.js library
  - Real-time visual charts of performance
  - Line graphs for trends
  - Bar charts for topic comparison
  
- **Database Queries**:
  ```sql
  SELECT topic, COUNT(*) as attempts, 
         AVG(is_correct) as accuracy, 
         AVG(time_taken) as avg_time
  FROM users_practiceactivity
  GROUP BY topic
  ```

---

### **PHASE 3: QUIZ SELECTION**
```
User Clicks "Start Quiz"
        ↓
┌─────────────────────────────────────────────────────────────┐
│  [3] Quiz Type Selection                                    │
├─────────────────────────────────────────────────────────────┤
│  Option A: Static Quiz (Fixed 10 Questions)                 │
│  Option B: AI-Adaptive Quiz (Dynamic AI Generated)          │
│  Option C: Weak Areas Quiz (Focused on Weaknesses)          │
└─────────────────────────────────────────────────────────────┘
```

**Tech Used:**
- **Django Views**: URL routing to different quiz flows
- **Frontend**: Radio button selection in HTML/CSS
- **Session State**: Stores user's choice in Django session

---

### **PHASE 4A: STATIC QUIZ FLOW**
```
User Selects "Static Quiz"
        ↓
┌─────────────────────────────────────────────────────────────┐
│  [4A] Load 10 Curated Questions                             │
├─────────────────────────────────────────────────────────────┤
│  Question Bank Source: questions.py                         │
│  - 10 handcrafted questions (Quant, Reasoning, etc)        │
│  - Difficulty levels: Easy, Medium, Hard                    │
│  - Randomized order (shuffled each session)                 │
│  - 4 multiple choice options per question                   │
└─────────────────────────────────────────────────────────────┘
        ↓
   User Answers Questions & Tracks Time
        ↓
┌─────────────────────────────────────────────────────────────┐
│  [4B] Validate & Store Responses                            │
├─────────────────────────────────────────────────────────────┤
│  Technology Stack:                                          │
│  ├─ Frontend: JavaScript timer for each question          │
│  ├─ Backend: Compare selected_option vs correct_answer    │
│  ├─ Database: Save to PracticeActivity model              │
│  └─ Calculation: Live accuracy percentage                 │
│                                                             │
│  Data Stored in PracticeActivity Table:                   │
│  ├─ user_id (Foreign Key)                                 │
│  ├─ question_id                                           │
│  ├─ topic (e.g., "Quantitative")                         │
│  ├─ selected_option (user's choice)                       │
│  ├─ correct_answer (right answer)                         │
│  ├─ is_correct (boolean)                                  │
│  ├─ time_taken (seconds)                                  │
│  └─ attempted_at (timestamp)                              │
└─────────────────────────────────────────────────────────────┘
        ↓
   Quiz Completes (10 Questions Done)
        ↓
┌─────────────────────────────────────────────────────────────┐
│  [4C] Generate Quiz Summary                                 │
├─────────────────────────────────────────────────────────────┤
│  Calculate Session Statistics:                              │
│  ├─ Total Questions: 10                                     │
│  ├─ Correct Answers: [Count]                                │
│  ├─ Accuracy: (Correct/Total) × 100                        │
│  ├─ Total Time: Sum of all time_taken                      │
│  └─ Performance Breakdown: By topic & difficulty            │
│                                                              │
│  Store QuizSession Record:                                  │
│  ├─ user_id                                                 │
│  ├─ total_questions = 10                                    │
│  ├─ correct_answers = [calculated]                          │
│  ├─ accuracy = [percentage]                                 │
│  ├─ total_time = [seconds]                                  │
│  └─ completed_at = [timestamp]                              │
└─────────────────────────────────────────────────────────────┘
        ↓
   Redirect to Quiz Summary Page
```

**Key Technologies:**

| Component | Tech | Purpose |
|-----------|------|---------|
| Question Bank | Python (questions.py) | Curated static questions |
| Randomization | Python `random.shuffle()` | Shuffle question order |
| Timer | JavaScript | Track time per question |
| Form Submission | HTML Form POST | Send answers to backend |
| Validation Logic | Django view functions | Check correct/incorrect |
| Data Storage | Django ORM | Save to PracticeActivity |
| Session Storage | QuizSession Model | Store quiz statistics |

---

### **PHASE 4B: AI-ADAPTIVE QUIZ FLOW**
```
User Selects "AI-Adaptive Quiz"
        ↓
┌─────────────────────────────────────────────────────────────┐
│  [5] Detect User's Weak Areas                               │
├─────────────────────────────────────────────────────────────┤
│  Module: analytics.py                                       │
│  Function: get_topic_statistics()                           │
│                                                              │
│  Calculates Weakness Score (0-1):                           │
│  ├─ Accuracy Factor (50% weight)                           │
│  │  weakness = (100 - accuracy) / 100                      │
│  ├─ Time Factor (30% weight)                               │
│  │  weakness = avg_time / 120 seconds                      │
│  └─ Consistency Factor (20% weight)                        │
│     weakness = (100 - consistency) / 100                   │
│                                                              │
│  Formula:                                                    │
│  weakness_score = (accuracy×0.5) + (time×0.3) +           │
│                    (consistency×0.2)                        │
│                                                              │
│  Output: List of topics ranked by weakness                 │
│  Example:                                                    │
│  {                                                           │
│    "topic": "Quantitative",                                │
│    "accuracy": 45%,                                         │
│    "weakness_score": 0.78  ← Very Weak                    │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│  [6] Call Groq AI API                                       │
├─────────────────────────────────────────────────────────────┤
│  Module: ai_generator.py                                    │
│  API: Groq (LLaMA 3.3 70B or LLaMA 3.1 8B)                │
│                                                              │
│  API Prompt Template:                                       │
│  "Generate 5 difficult questions on [WEAK_TOPIC]           │
│   in [DIFFICULTY] level. Format as JSON with:             │
│   - question                                                │
│   - options (array of 4)                                    │
│   - correct_answer (0-3 index)                             │
│   - explanation"                                            │
│                                                              │
│  Groq Features:                                             │
│  ├─ Free API (no billing)                                  │
│  ├─ Fast inference (~70ms latency)                         │
│  ├─ Open source model (LLaMA)                              │
│  └─ Context-aware generation                               │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│  [7] Parse & Display AI Questions                           │
├─────────────────────────────────────────────────────────────┤
│  Response Format:                                            │
│  {                                                           │
│    "question": "What is the derivative of x^3?",           │
│    "options": [                                             │
│      "3x^2",                                                │
│      "x^3",                                                 │
│      "3",                                                   │
│      "0"                                                    │
│    ],                                                        │
│    "correct_answer": 0,  ← Index into options array        │
│    "difficulty": "Hard",                                    │
│    "explanation": "By power rule..."                        │
│  }                                                           │
│                                                              │
│  Fallback: If API fails, use static questions              │
└─────────────────────────────────────────────────────────────┘
        ↓
   User Answers AI-Generated Questions
        ↓
   Same as Static Quiz: Validate, Score, Store
```

**Key Technologies:**

| Component | Tech | Purpose |
|-----------|------|---------|
| Weak Area Detection | Python analytics.py | Identify problem topics |
| AI Model | Groq API + LLaMA | Generate contextual questions |
| API Communication | Python Groq client | Call LLM endpoints |
| Response Parsing | JSON + Regex | Extract question data |
| Error Handling | Try/Except + Fallback | Use static if AI fails |
| Caching | Django cache | Store API responses |

**Groq API Advantages:**
- ✅ Free (no OpenAI/Gemini costs)
- ✅ Fast (50-100ms inference)
- ✅ No rate limits for dev
- ✅ Open source models
- ✅ High accuracy

---

### **PHASE 5: WEAK AREAS ANALYSIS**
```
After Quiz Completion
        ↓
┌─────────────────────────────────────────────────────────────┐
│  [8] Analyze Weak Topics                                    │
├─────────────────────────────────────────────────────────────┤
│  Module: analytics.py                                       │
│  Function: get_topic_statistics()                           │
│                                                              │
│  Weak Area Criteria:                                        │
│  ├─ Accuracy < 50% (consistently wrong)                    │
│  ├─ Avg Time > 60 seconds (struggling)                     │
│  └─ Consistency Score < 50% (not improving)                │
│                                                              │
│  Output: Ranked list by weakness score                      │
│  {                                                           │
│    "topic": "Logical Reasoning",                            │
│    "accuracy": 35%,                                         │
│    "avg_time": 75s,                                         │
│    "weakness_score": 0.85,  ← Critical!                    │
│    "action": "Needs immediate focus"                        │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
        ↓
   Display Weak Areas Page
```

---

### **PHASE 6: AI RECOMMENDATIONS**
```
When User Views Weak Areas
        ↓
┌─────────────────────────────────────────────────────────────┐
│  [9] Generate AI Recommendations                            │
├─────────────────────────────────────────────────────────────┤
│  Module: analytics.py                                       │
│  Function: generate_recommendations()                       │
│                                                              │
│  Input: Weak area topics + weakness scores                  │
│                                                              │
│  Call Groq AI to Generate Study Plan:                       │
│  "Student is weak in [TOPIC] with [SCORE]%.                │
│   Generate 5 specific study recommendations:               │
│   - Concept to review                                       │
│   - Practice strategy                                       │
│   - Time allocation                                         │
│   - Resource suggestion"                                    │
│                                                              │
│  Recommendations Generated:                                 │
│  ├─ Topic Review: What to study                            │
│  ├─ Practice Focus: Problem types to solve                 │
│  ├─ Time Goal: How long to practice                        │
│  ├─ Difficulty Progression: Easy → Hard                    │
│  └─ Urgency Level: Critical/High/Medium                    │
│                                                              │
│  Display Format:                                            │
│  ┌──────────────────────────────┐                          │
│  │ URGENT: Quantitative (85%)   │                          │
│  │ ├─ Review: Algebra basics    │                          │
│  │ ├─ Practice: Linear equations│                          │
│  │ ├─ Time: 2 hrs/day           │                          │
│  │ └─ Next: Try Hard Difficulty │                          │
│  └──────────────────────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ TECHNOLOGY STACK BREAKDOWN

### **FRONTEND LAYER**
```
┌─────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                        │
├─────────────────────────────────────────────────────────────┤
│ Technology          │ Purpose                                │
├─────────────────────┼────────────────────────────────────────┤
│ HTML5               │ Page structure (forms, layouts)        │
│ CSS3                │ Styling & responsive design           │
│ JavaScript          │ Interactivity & timers                │
│ Chart.js            │ Analytics visualization               │
│ Responsive Design   │ Mobile, tablet, desktop support       │
└─────────────────────────────────────────────────────────────┘

Key Features:
- Quiz Timer: JavaScript countdown for each question
- Form Validation: Client-side + server-side checks
- Real-time Charts: Display trends using Chart.js
- Session Management: Maintain user state across pages
```

### **BACKEND LAYER**
```
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION SERVER                        │
├─────────────────────────────────────────────────────────────┤
│ Technology          │ Purpose                                │
├─────────────────────┼────────────────────────────────────────┤
│ Django 6.0          │ Web framework & ORM                    │
│ Python 3.x          │ Server-side logic                      │
│ Django Auth         │ User authentication & permissions      │
│ Django ORM          │ Database abstraction layer             │
│ Django Middleware   │ Request/response processing            │
│ Decorators          │ Authentication & HTTP methods          │
└─────────────────────────────────────────────────────────────┘

Modules:
1. views.py (13 endpoints)
   - login_page()        → User authentication
   - dashboard()         → Analytics display
   - static_quiz()       → 10-question quiz
   - adaptive_quiz()     → AI-generated quiz
   - weak_areas()        → Weakness analysis
   - recommendations()   → AI suggestions
   - quiz_summary()      → Results page
   - logout_user()       → Session cleanup

2. models.py (Data Models)
   - User              → Django built-in (auth)
   - PracticeActivity  → Individual question attempts
   - QuizSession       → Complete quiz results

3. analytics.py (Business Logic)
   - get_topic_statistics()      → Aggregate quiz data
   - calculate_weakness_score()  → Rank weak areas
   - generate_recommendations()  → AI study suggestions

4. ai_generator.py (AI Integration)
   - _get_groq_client()          → Connect to Groq API
   - generate_adaptive_questions() → Call LLM for questions

5. questions.py (Question Bank)
   - get_all_questions()         → Static question pool
```

### **DATA LAYER**
```
┌─────────────────────────────────────────────────────────────┐
│                      DATABASE (SQLite3)                      │
├─────────────────────────────────────────────────────────────┤
│ Table               │ Purpose                                │
├─────────────────────┼────────────────────────────────────────┤
│ auth_user           │ User accounts & passwords              │
│ users_practiceactivity  │ Individual question attempts    │
│ users_quizsession   │ Quiz session summaries                 │
│ django_session      │ Session storage                        │
└─────────────────────────────────────────────────────────────┘

PracticeActivity Schema:
- id (PrimaryKey)
- user_id (Foreign Key → User)
- question_id
- topic (VARCHAR 100)
- difficulty (VARCHAR 20)
- selected_option (INT)
- correct_answer (INT)
- is_correct (BOOLEAN)
- time_taken (INT, seconds)
- attempted_at (DATETIME)

QuizSession Schema:
- id (PrimaryKey)
- user_id (Foreign Key → User)
- total_questions
- correct_answers
- accuracy (FLOAT %)
- total_time (INT, seconds)
- completed_at (DATETIME)
```

### **EXTERNAL APIs**
```
┌─────────────────────────────────────────────────────────────┐
│                      GROQ API (LLM)                          │
├─────────────────────────────────────────────────────────────┤
│ Component           │ Details                                │
├─────────────────────┼────────────────────────────────────────┤
│ API Provider        │ Groq (groq.com)                       │
│ Models Available    │ LLaMA 3.3 70B (fast)                  │
│                     │ LLaMA 3.1 8B (ultra-fast)             │
│ Authentication      │ API Key (environment variable)        │
│ Request Format      │ JSON with prompt & parameters         │
│ Response Format     │ JSON with generated text              │
│ Rate Limit          │ None for free tier                    │
│ Latency             │ 50-150ms per request                  │
│ Cost                │ FREE (open source model)              │
└─────────────────────────────────────────────────────────────┘

Usage:
1. User weak areas identified
2. Groq prompt generated with topic/difficulty
3. API called via Python Groq client
4. Response parsed as JSON
5. Questions displayed to user
6. Fallback to static questions if API fails
```

---

## 📊 DATA FLOW DIAGRAM

```
USER INTERACTION
      │
      ├─→ [Login] → Django Auth → SQLite User Table
      │
      ├─→ [View Dashboard] → analytics.py → Query PracticeActivity
      │                      → Aggregate data → Chart.js visualization
      │
      ├─→ [Take Static Quiz]
      │   ├─ questions.py → Load 10 questions
      │   ├─ Shuffle with random.shuffle()
      │   ├─ User answers → JavaScript timer
      │   ├─ Submit form → views.py validation
      │   ├─ Save to PracticeActivity → SQLite INSERT
      │   └─ Create QuizSession → SQLite INSERT
      │
      ├─→ [Take AI-Adaptive Quiz]
      │   ├─ analytics.py → Detect weak topics
      │   ├─ ai_generator.py → Call Groq API
      │   ├─ Groq API → Generate contextual questions
      │   ├─ Parse JSON response
      │   ├─ User answers questions
      │   ├─ Save attempts → PracticeActivity
      │   └─ Create session record
      │
      ├─→ [View Weak Areas]
      │   ├─ analytics.py → Calculate weakness scores
      │   ├─ Rank topics by weakness
      │   └─ Display prioritized list
      │
      └─→ [Get Recommendations]
          ├─ Get weak areas data
          ├─ Call Groq with weak topics
          ├─ Generate study plan
          └─ Display to user

DATABASE OPERATIONS:
- All data persisted in SQLite3
- Django ORM handles queries
- Migrations track schema changes
- Indexes on user_id & attempted_at for fast queries
```

---

## 🔐 SECURITY FEATURES

```
Authentication:
├─ Django Auth System
│  ├─ Password hashing (PBKDF2)
│  ├─ Session tokens
│  └─ CSRF protection
├─ Login decorators (@login_required)
│  ├─ Blocks unauthorized access
│  └─ Redirects to login page
└─ URL validation
   ├─ Prevents open redirect attacks
   └─ url_has_allowed_host_and_scheme()

Data Protection:
├─ SQLite3 database (local)
├─ Foreign keys prevent orphaned data
└─ User isolation (each sees own data)

API Security:
├─ Groq API key stored in environment variables
├─ Never exposed in code
└─ Rate limiting built into Groq free tier
```

---

## 🚀 DEPLOYMENT STACK

```
┌─────────────────────────────────────────────────────────────┐
│                   PRODUCTION SETUP                           │
├─────────────────────────────────────────────────────────────┤
│ Component           │ Technology                             │
├─────────────────────┼────────────────────────────────────────┤
│ Web Server          │ Gunicorn (WSGI server)                │
│ Static Files        │ WhiteNoise (CDN alternative)          │
│ Platform            │ Heroku (Procfile configured)          │
│ Database            │ SQLite3 (can scale to PostgreSQL)     │
│ Environment Vars    │ .env file (not in repo)               │
│ CORS                │ Configured for cross-origin requests  │
└─────────────────────────────────────────────────────────────┘

Deployment Flow:
1. Code pushed to Heroku
2. Procfile triggers: gunicorn backend.wsgi:application
3. WhiteNoise serves static files (CSS, JS, images)
4. Django processes requests
5. Data stored in SQLite3 (Heroku ephemeral storage)
6. Scale to PostgreSQL for production scaling
```

---

## 📈 PERFORMANCE METRICS

```
Response Time Targets:
├─ Page Load: < 500ms
├─ Quiz Submission: < 1s
├─ Groq API Call: 50-150ms
├─ Dashboard Render: < 2s
└─ Analytics Calculation: < 500ms

Database Indexes:
├─ user_id (most queries filter by user)
├─ attempted_at (for time-based queries)
├─ topic (for topic-based analysis)
└─ is_correct (for accuracy calculations)

Caching Strategy:
├─ Static questions: Cached in Python module
├─ Groq responses: Django cache (configurable TTL)
├─ User statistics: Recalculated on quiz completion
└─ Session data: Django session cache
```

---

## 🎯 KEY WORKFLOW SUMMARY

```
1. USER REGISTERS/LOGS IN
   └─→ Django Auth validates credentials
       └─→ Session created, redirected to dashboard

2. USER VIEWS DASHBOARD
   └─→ analytics.py queries PracticeActivity
       └─→ Calculates stats & charts
           └─→ Chart.js renders visualization

3. USER SELECTS QUIZ TYPE
   ├─→ STATIC: questions.py loads 10 fixed questions
   │   └─→ User answers → Saved to PracticeActivity
   │
   └─→ ADAPTIVE: analytics.py detects weaknesses
       └─→ Groq API generates contextual questions
           └─→ User answers → Saved to database

4. USER COMPLETES QUIZ
   └─→ QuizSession record created with stats
       └─→ Redirected to summary page

5. USER CHECKS WEAK AREAS
   └─→ analytics.py calculates weakness scores
       └─→ Groq generates study recommendations
           └─→ Display actionable study plan

6. LOOP: Take more quizzes → Get better insights
```

---

## 💡 HOW IT ALL WORKS TOGETHER

### **The Intelligence Loop**

```
Student Performance Data
        ↓
   Collected in PracticeActivity
        ↓
   analytics.py analyzes patterns
        ↓
   Weakness scores calculated
        ↓
   Groq API generates targeted questions
        ↓
   Student practices weak areas
        ↓
   Performance improves
        ↓
   Loop: More practice → Better insights → Improvement
```

### **Key Innovation**

This platform transforms passive quiz-taking into **active, intelligence-driven learning**:

- ❌ **Before**: Student takes quiz, forgets results
- ✅ **After**: System detects weaknesses → Generates personalized questions → Tracks improvement

---

## 🎓 EDUCATIONAL VALUE

```
Traditional Quiz Platform:
├─ Question bank
├─ Score calculation
└─ End (no insights)

AI Learning Platform:
├─ Adaptive questions (AI)
├─ Score calculation
├─ Weak area detection (ML)
├─ Personalized recommendations (AI)
├─ Historical tracking
└─ Performance trends
└─ Study plan generation (AI)
```

---

## 📱 RESPONSIVE DESIGN

```
Frontend Adaptation:
├─ Mobile (< 768px)
│  ├─ Single-column layout
│  ├─ Touch-friendly buttons
│  └─ Optimized timer display
├─ Tablet (768px - 1024px)
│  ├─ Two-column layout
│  └─ Larger buttons
└─ Desktop (> 1024px)
   ├─ Multi-column dashboard
   ├─ Side-by-side charts
   └─ Full feature display
```

---

## 🔄 COMPLETE USER JOURNEY (DETAILED)**

```
STEP 1: DISCOVERY
User visits http://127.0.0.1:8000/
    ↓
Redirected to /login
    ↓
Sees login form + register link

STEP 2: REGISTRATION
Click "Register New Account"
    ↓
Fill: Username, Password, Confirm Password
    ↓
Django validates password strength
    ↓
Check for duplicate username
    ↓
User account created
    ↓
Redirect to login page

STEP 3: LOGIN
Fill: Username, Password
    ↓
Django Auth authenticates
    ↓
Session created (stored in DB)
    ↓
Redirect to /dashboard

STEP 4: DASHBOARD VIEW
Analytics displayed:
- Overall accuracy % (aggregated from all quizzes)
- Quiz attempt count
- Average time per question
- Performance chart (Chart.js)
- Topic-wise breakdown

Backend flow:
views.py dashboard() → 
analytics.get_topic_statistics(user) → 
PracticeActivity.objects.filter(user=user) →
SQLite query →
Aggregate with Django ORM →
Pass data to template → 
Chart.js renders visualization

STEP 5: CHOOSE QUIZ TYPE
Link: "Start New Quiz" / "Take Adaptive Quiz" / "Practice Weak Areas"

STEP 6A: STATIC QUIZ
views.py static_quiz() →
questions.py get_all_questions() →
random.shuffle() →
Template renders 10 questions →
JavaScript timer for each question →
User clicks "Next" →
Selected option sent to backend via AJAX/Form →
views.py validates: selected_option == correct_answer? →
PracticeActivity record created →
Repeat for 10 questions →
Finally, QuizSession record created with:
- total_questions = 10
- correct_answers = [count]
- accuracy = (correct/10) * 100
- total_time = sum of all time_taken
Redirect to quiz_summary.html

STEP 6B: ADAPTIVE QUIZ
views.py adaptive_quiz() →
analytics.get_topic_statistics(user) →
Identify weakest topic (highest weakness_score) →
ai_generator.generate_adaptive_questions(topic) →
Create Groq prompt: "Generate 5 hard questions on [TOPIC]" →
_get_groq_client() →
Groq API call with API key →
Receive JSON with questions array →
Parse and validate JSON →
Fallback to static questions if API fails →
Display to user (same as static quiz) →
Store responses →
Same as above: Create QuizSession

STEP 7: QUIZ SUMMARY
Display:
- Score: X/10
- Accuracy: %
- Total time: seconds
- Topic breakdown
- Chart of results
- Option to retake or go to dashboard

STEP 8: WEAK AREAS PAGE
views.py weak_areas() →
analytics.get_topic_statistics(user) →
Calculate weakness_score for each topic:
  weakness = (0.5 * accuracy_weakness) +
             (0.3 * time_weakness) +
             (0.2 * consistency_weakness)
Sort by weakness_score DESC →
Display topics with:
  - Topic name
  - Accuracy %
  - Weakness score (0-1)
  - Action recommended (Critical/High/Medium)
Chart visualization of weak topics

STEP 9: RECOMMENDATIONS PAGE
views.py recommendations() →
Get user's weak topics →
For each weak topic:
  Call ai_generator.generate_recommendations(topic, weakness_score) →
  Groq API prompt: "Student weak in [TOPIC] with [SCORE]%. Give 5 study tips" →
  Parse AI response →
  Display study plan:
    - Concept review needed
    - Practice problem types
    - Time allocation recommendation
    - Difficulty progression
    - Urgency level

STEP 10: CONTINUED LEARNING LOOP
User practices on weak areas →
Takes more quizzes →
PracticeActivity records accumulate →
Weakness scores change based on new performance →
Recommendations update →
Personalization improves over time

STEP 11: LOGOUT
Click "Logout" button →
views.py logout_user() →
Session deleted →
Redirect to login page
```

---

## 📋 TECH SUMMARY TABLE

| Layer | Component | Technology | Function |
|-------|-----------|-----------|----------|
| **Frontend** | UI | HTML5, CSS3, JS | User interface |
| | Charts | Chart.js | Visualizations |
| | Timer | JavaScript | Question countdown |
| | Responsive | CSS Media Queries | Mobile support |
| **Backend** | Framework | Django 6.0 | Web application |
| | Language | Python 3.x | Server logic |
| | Auth | Django Auth | User management |
| | ORM | Django ORM | Database queries |
| | Views | 13 Endpoints | Request handlers |
| **Database** | DBMS | SQLite3 | Data persistence |
| | Models | 3 Custom Models | Data structure |
| | Sessions | Django Session | State management |
| **AI/ML** | Analytics | analytics.py | Weakness detection |
| | AI Model | Groq API (LLaMA) | Question generation |
| | Integration | Python Groq Client | API communication |
| **Deployment** | Server | Gunicorn | WSGI server |
| | Static Files | WhiteNoise | File serving |
| | Platform | Heroku | Cloud hosting |

---

## 🎯 SUCCESS METRICS

```
For Students:
✓ Awareness of weak areas (clearly identified)
✓ Personalized learning path (AI recommendations)
✓ Measurable improvement (tracked over time)
✓ Reduced study time (focused practice)

For Platform:
✓ Data-driven insights (analytics module)
✓ AI-powered adaptation (Groq integration)
✓ Scalable architecture (Django + SQL)
✓ Cost-effective (free Groq API)
```

---

**End of Presentation**

*For technical deep-dives, refer to individual module documentation in the codebase.*
