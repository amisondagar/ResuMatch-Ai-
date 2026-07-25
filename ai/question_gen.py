"""
ai/question_gen.py — Interview Question Generator
ResumeMatch.ai

Generates relevant interview questions based on the candidate's
matched skills and the job description.

HOW IT WORKS:
  1. Look at matched skills between resume and JD
  2. Pull question templates for each skill category
  3. Add JD-specific behavioural questions
  4. Return a curated list of 10-15 questions

INTERVIEW TIP:
"This is a rule-based generation system — we map skills to predefined
question banks. A more advanced version could use an LLM API."
"""

import random

# ── Question Templates Per Skill Category ─────────────────────────────────

QUESTION_BANK = {
    'python': [
        "Explain the difference between a list and a tuple in Python.",
        "What are Python decorators and how do you use them?",
        "How does Python's GIL (Global Interpreter Lock) work?",
        "What is the difference between @staticmethod and @classmethod?",
        "Explain Python's memory management and garbage collection.",
        "How would you handle concurrency in Python? (threading vs asyncio)",
        "What are generators and when would you use them?",
    ],
    'java': [
        "Explain the four pillars of Object-Oriented Programming with Java examples.",
        "What is the difference between an interface and an abstract class?",
        "How does Java's garbage collector work?",
        "Explain the Java Collections Framework.",
        "What is the difference between synchronized and volatile in Java?",
    ],
    'javascript': [
        "Explain event bubbling and event capturing in JavaScript.",
        "What is the difference between == and === in JavaScript?",
        "How does the JavaScript event loop work?",
        "Explain closures and give a practical example.",
        "What are Promises and how do they differ from async/await?",
    ],
    'react': [
        "What is the virtual DOM and how does React use it?",
        "Explain the React component lifecycle.",
        "What are React hooks? Explain useState and useEffect.",
        "How do you manage state in large React applications?",
        "What is the difference between controlled and uncontrolled components?",
    ],
    'machine learning': [
        "Explain overfitting and how to prevent it.",
        "What is the bias-variance tradeoff?",
        "How does gradient descent work?",
        "Explain cross-validation and why it's important.",
        "What is the difference between supervised and unsupervised learning?",
    ],
    'deep learning': [
        "How does backpropagation work in neural networks?",
        "What is the vanishing gradient problem and how do you solve it?",
        "Explain the difference between CNN and RNN.",
        "What are attention mechanisms and transformers?",
        "When would you use transfer learning?",
    ],
    'sql': [
        "What is the difference between INNER JOIN and OUTER JOIN?",
        "Explain database normalization (1NF, 2NF, 3NF).",
        "How do you optimize a slow SQL query?",
        "What are indexes and when should you use them?",
        "Explain ACID properties in databases.",
    ],
    'aws': [
        "Explain the difference between EC2, Lambda, and ECS.",
        "How does auto-scaling work in AWS?",
        "What is the difference between S3 and EBS?",
        "How would you design a highly available architecture on AWS?",
        "Explain IAM roles and policies.",
    ],
    'docker': [
        "What is the difference between a Docker image and a container?",
        "How do Docker volumes work?",
        "Explain multi-stage Docker builds.",
        "What is Docker Compose and when would you use it?",
    ],
    'kubernetes': [
        "Explain the Kubernetes architecture (master, nodes, pods).",
        "What is the difference between a Deployment and a StatefulSet?",
        "How does Kubernetes handle service discovery?",
        "What are ConfigMaps and Secrets in Kubernetes?",
    ],
    'flask': [
        "How do you structure a large Flask application?",
        "What are Flask Blueprints and why use them?",
        "How do you handle authentication in Flask?",
        "Explain Flask's application context vs request context.",
    ],
    'django': [
        "Explain the Django ORM and how it maps to database tables.",
        "What is Django middleware and how does it work?",
        "How do Django signals work?",
        "Explain Django REST Framework serializers.",
    ],
    'data science': [
        "Walk me through your typical data analysis workflow.",
        "How do you handle missing data in a dataset?",
        "Explain the difference between correlation and causation.",
        "How do you communicate insights to non-technical stakeholders?",
    ],
    'agile': [
        "Describe your experience working in Agile/Scrum teams.",
        "How do you handle scope creep in a sprint?",
        "What is the difference between Scrum and Kanban?",
        "How do you prioritize a product backlog?",
    ],
    'leadership': [
        "Tell me about a time you led a team through a difficult project.",
        "How do you handle conflict within your team?",
        "Describe your approach to mentoring junior developers.",
    ],
    'git': [
        "Explain the difference between git merge and git rebase.",
        "How do you resolve merge conflicts?",
        "Describe your branching strategy for a team project.",
    ],
}

# ── General behavioural questions ─────────────────────────────────────────

BEHAVIOURAL_QUESTIONS = [
    "Tell me about yourself and your most recent project.",
    "Describe a challenging technical problem you solved and how.",
    "How do you stay updated with new technologies in your field?",
    "Tell me about a time you worked under a tight deadline.",
    "Where do you see yourself in 5 years?",
    "What is your greatest professional achievement?",
    "How do you handle feedback and criticism on your work?",
    "Describe a situation where you had to learn something quickly.",
    "What motivates you to do your best work?",
    "Why are you interested in this particular role?",
]


def generate_questions(matched_skills, jd_text='', count=12):
    """
    Generate interview questions based on matched skills.

    Args:
        matched_skills (list): Skills found in both resume and JD
        jd_text (str):         Full JD text for context
        count (int):           Number of questions to return

    Returns:
        list of dict: [{category, question}, ...]
    """
    questions = []

    # ── Technical questions from matched skills ────────────────────────────
    skills_used = set()
    for skill in matched_skills:
        skill_key = skill.lower()
        if skill_key in QUESTION_BANK and skill_key not in skills_used:
            bank = QUESTION_BANK[skill_key]
            selected = random.sample(bank, min(2, len(bank)))
            for q in selected:
                questions.append({
                    'category': 'Technical',
                    'skill':    skill,
                    'question': q
                })
            skills_used.add(skill_key)
        if len(questions) >= count - 3:
            break

    # ── Fuzzy match for multi-word skills ─────────────────────────────────
    if len(questions) < count - 3:
        for bank_key, bank_qs in QUESTION_BANK.items():
            if bank_key not in skills_used:
                for skill in matched_skills:
                    if bank_key in skill.lower() or skill.lower() in bank_key:
                        q = random.choice(bank_qs)
                        questions.append({
                            'category': 'Technical',
                            'skill':    bank_key.title(),
                            'question': q
                        })
                        skills_used.add(bank_key)
                        break
            if len(questions) >= count - 3:
                break

    # ── Behavioural questions ──────────────────────────────────────────────
    behavioural = random.sample(BEHAVIOURAL_QUESTIONS,
                                min(3, len(BEHAVIOURAL_QUESTIONS)))
    for q in behavioural:
        questions.append({
            'category': 'Behavioural',
            'skill':    'General',
            'question': q
        })

    return questions[:count]
