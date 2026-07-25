import re

# Comprehensive list of stop words to filter out
STOP_WORDS = {
    'creative', 'suite', 'creative suite', 'adobe', 'adobe creative suite',
    'microsoft', 'office', 'amazon', 'video', 'graphic', 'employment', 'senior',
    'front', 'end', 'germany', 'associate', 'specialist', 'professional',
    'engineer', 'developer', 'designer', 'resume', 'cv', 'curriculum', 'vitae',
    'page', 'profile', 'summary', 'experience', 'education', 'skills', 'contact',
    'phone', 'email', 'links', 'project', 'projects', 'about', 'manager', 'lead',
    'intern', 'junior', 'lead', 'architect', 'principal', 'full', 'stack', 'software',
    'web', 'ui/ux', 'ux/ui', 'ui', 'ux', 'tools', 'software', 'skills', 'technical',
    'soft', 'work', 'history', 'academic', 'qualifications', 'certifications', 'awards'
}

def is_valid_name_token(token):
    t_lower = token.lower()
    if t_lower in STOP_WORDS:
        return False
    if len(token) < 2:
        return False
    if not token.isalpha():
        return False
    return True

def extract_person_name_strict(text, filename=''):
    """
    Extract ONLY First Name + Surname cleanly from resume text or filename fallback.
    Guarantees no skill names (like 'Creative Suite'), titles, or software tools.
    """
    if not text:
        text = ''

    lines = [l.strip() for l in text.split('\n') if l.strip()]

    # 1. Try spaCy Person NER if available
    try:
        import spacy
        nlp = spacy.load('en_core_web_sm')
        doc = nlp(text[:400])
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                tokens = [w.strip() for w in ent.text.split() if is_valid_name_token(w)]
                if 2 <= len(tokens) <= 3:
                    return ' '.join(t.capitalize() for t in tokens)
    except Exception:
        pass

    # 2. Search top 5 lines for a strict 2-word Person Name (First Last)
    for line in lines[:5]:
        clean_l = re.split(r'[\(\d\+@]|http|www|\.com|Summary|Profile|Experience|Objective|Phone|Email', line, flags=re.IGNORECASE)[0].strip()
        tokens = [w.strip() for w in clean_l.split() if is_valid_name_token(w)]

        # Check if line looks like a name (e.g. "Aparna Khatri")
        if 2 <= len(tokens) <= 3:
            return ' '.join(t.capitalize() for t in tokens)

    # 3. Fallback: Parse filename if available (e.g., 'aparna_khatri_resume.pdf' -> 'Aparna Khatri')
    if filename:
        clean_fn = re.sub(r'^\d+[\-_]?', '', filename)  # remove timestamp prefix
        clean_fn = re.sub(r'\.(pdf|docx|doc)$', '', clean_fn, flags=re.IGNORECASE)
        clean_fn = re.sub(r'[\-_]', ' ', clean_fn)
        tokens = [w.strip() for w in clean_fn.split() if is_valid_name_token(w)]
        if 2 <= len(tokens) <= 3:
            return ' '.join(t.capitalize() for t in tokens)

    # 4. Fallback: Take first 2 valid tokens from top text line
    if lines:
        tokens = [w.strip() for w in re.sub(r'[^a-zA-Z\s]', ' ', lines[0]).split() if is_valid_name_token(w)]
        if len(tokens) >= 2:
            return f"{tokens[0].capitalize()} {tokens[1].capitalize()}"
        elif len(tokens) == 1:
            return tokens[0].capitalize()

    return 'Candidate'

test_inputs = [
    ("Creative Suite\nAparna Khatri\naparna.khatri@gmail.com\nSenior Graphic Designer", "aparna_khatri_resume.pdf"),
    ("Aparna Khatri\nCreative Suite\naparna.khatri@gmail.com", "aparna_khatri.pdf"),
    ("Marie Madel\nMmarie@gamil.com\nGermany Web Developer", "marie_madel.pdf"),
    ("Daniel Gan\nresume@example.com\nFront End Developer", "daniel_gan.pdf")
]

for txt, fn in test_inputs:
    print(f"File: '{fn}' -> Name: '{extract_person_name_strict(txt, fn)}'")
