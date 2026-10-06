import re

def analyze_resume(text, data):
    lower = text.lower()
    sections = {
        "education": bool(data["education"]),
        "skills": bool(data["skills"]),
        "projects": bool(data["projects"]),
        "certifications": bool(data["certifications"]),
        "experience": bool(data["experience"])
    }
    findings = []
    for name, present in sections.items():
        if not present:
            findings.append({"type":"warning","message":f"Consider adding a clear {name} section if it applies to you."})
    if len(text.split()) < 180:
        findings.append({"type":"warning","message":"The resume appears short; add relevant evidence without adding filler."})
    if not re.search(r"\b(developed|built|created|implemented|designed|analyzed|automated)\b", lower):
        findings.append({"type":"warning","message":"Project bullets could use stronger action verbs such as developed, implemented, or automated."})
    if not re.search(r"\b\d+%|\b\d+\s*(users|records|datasets|projects|months|days)\b", lower):
        findings.append({"type":"warning","message":"Where truthful, quantify outcomes such as users, records, accuracy, time saved, or dataset size."})
    improvements = []
    for p in (data.get("project_details") or [])[:6]:
        issues = []
        desc = p["description"]
        if not p["skills"]:
            issues.append("name the technologies you used")
        if len(desc.split()) < 12:
            issues.append("describe what you built and your own contribution")
        if not re.search(r"\d", desc):
            issues.append("add a measurable result (accuracy, users, records, time saved)")
        if not re.search(r"\b(developed|built|created|implemented|designed|analy[sz]ed|automated|trained|deployed|integrated)\b", desc.lower()):
            issues.append("start with a strong action verb")
        if issues:
            improvements.append({
                "original": p["text"],
                "suggestion": f"{p['name']}: " + "; ".join(issues) + ". Use: Action + Technology + Your contribution + Result.",
                "reason": "Each project is reviewed on its own so recruiters can see exactly what you did."
            })
    if not improvements:
        improvements.append({
            "original": "Project descriptions",
            "suggestion": "Use: Action + Technology + Your Contribution + Result.",
            "reason": "This structure makes project work easier for recruiters to understand."
        })
    return {"findings": findings, "improvements": improvements, "sections": sections}
