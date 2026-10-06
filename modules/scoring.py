def calculate_resume_score(data, analysis):
    score = 0
    score += min(25, len(data["skills"]) * 2.5)
    score += min(25, len(data["projects"]) * 8)
    score += 15 if data["education"] else 0
    score += 15 if data["experience"] else 0
    score += 10 if data["certifications"] else 0
    score += 10 if data["email"] and data["phone"] else 5 if data["email"] else 0
    penalty = min(15, len(analysis["findings"]) * 2)
    return max(0, min(100, round(score - penalty)))
