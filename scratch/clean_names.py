import sqlite3
import re

stop_words = {
    'amazon', 'video', 'graphic', 'employment', 'senior', 'front', 'germany',
    'end', 'associate', 'specialist', 'professional', 'engineer', 'developer',
    'designer', 'resume', 'cv', 'curriculum', 'vitae', 'page', 'profile',
    'summary', 'experience', 'education', 'skills', 'contact', 'phone',
    'email', 'links', 'project', 'projects', 'about', 'manager', 'lead'
}

def clean_name(n):
    if not n:
        return 'Candidate'
    tokens = [t for t in re.sub(r'[^a-zA-Z\s]', ' ', str(n)).split() if t.lower() not in stop_words and len(t) >= 2]
    if len(tokens) >= 2:
        return f"{tokens[0].capitalize()} {tokens[1].capitalize()}"
    elif tokens:
        return tokens[0].capitalize()
    return str(n)

db_path = 'database/resumematch.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

candidates = cursor.execute("SELECT id, name FROM candidates").fetchall()
updated = 0
for cand_id, old_name in candidates:
    new_name = clean_name(old_name)
    if old_name != new_name:
        cursor.execute("UPDATE candidates SET name=? WHERE id=?", (new_name, cand_id))
        try:
            cursor.execute("UPDATE scores SET name=? WHERE candidate_id=?", (new_name, cand_id))
        except Exception:
            pass
        updated += 1
        print(f"Cleaned candidate: '{old_name}' -> '{new_name}'")

conn.commit()
conn.close()
print(f"Total candidate names updated: {updated}")
