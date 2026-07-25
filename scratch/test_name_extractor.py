import spacy
import re

nlp = spacy.load('en_core_web_sm')

test_cases = [
    "Aparna Khatri\naparna.khatri@gmail.com\nSenior Graphic Designer",
    "Marie Madel\nMmarie@gamil.com\nGermany Web Developer",
    "Daniel Gan\nresume@example.com\nFront End Developer",
    "Michelle Smith\nemail@email.com\nEmployment Software Professional",
    "Jason Miller\nemail@email.com\nAmazon Associate",
    "Kristen Connelly\nemail@email.com\nVideo Production",
    "Nathalie Nova\nemail@email.com\nGraphic Designer"
]

def extract_clean_person_name(text):
    if not text:
        return 'Candidate'

    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if not lines:
        return 'Candidate'

    first_line = lines[0]
    clean_line = re.split(r'[\(\d\+@]|http|www|\.com|Summary|Profile|Experience|Objective|Phone|Email', first_line, flags=re.IGNORECASE)[0].strip()

    # Rule 1: spaCy NER on top header
    doc = nlp(text[:250])
    for ent in doc.ents:
        if ent.label_ == 'PERSON':
            words = ent.text.strip().split()
            if 2 <= len(words) <= 3 and all(w.isalpha() for w in words):
                return ' '.join(w.capitalize() for w in words)

    # Rule 2: Strictly take first line if 2 capitalization tokens (First Last)
    words = [w.strip() for w in clean_line.split() if w.strip().isalpha()]
    if 2 <= len(words) <= 3:
        return ' '.join(w.capitalize() for w in words)

    if len(words) == 1:
        return words[0].capitalize()

    return 'Candidate'

for tc in test_cases:
    print(f"Extracted: '{extract_clean_person_name(tc)}'")
