def build_skill_gap(resume_skills, required_skills, match):
    """Prioritised gaps. High = required skill missing; Medium = required skill only partly covered or preferred skill missing."""
    details = match.get("skill_details")
    if not details:  # older match results without per-skill details
        missing = match.get("missing_skills", [])
        high = missing[:max(1, len(missing) // 2)] if missing else []
        return {"strengths": match.get("matching_skills", []), "high_priority": high,
                "medium_priority": missing[len(high):], "low_priority": [], "details": []}
    high = [d["skill"] for d in details if d["importance"] == "required" and d["status"] == "missing"]
    medium = ([d["skill"] for d in details if d["importance"] == "required" and d["status"] == "partial"] +
              [d["skill"] for d in details if d["importance"] == "preferred" and d["status"] == "missing"])
    low = [d["skill"] for d in details if d["importance"] == "preferred" and d["status"] == "partial"]
    strengths = [d["skill"] for d in details if d["status"] == "matched"]
    gaps = []
    for d in details:
        if d["status"] == "matched":
            continue
        if d["status"] == "partial":
            reason = f"You have related skills ({', '.join(d['via'])}) but not {d['skill']} itself."
        else:
            reason = f"{d['skill']} is {'required' if d['importance'] == 'required' else 'preferred'} and is not on your resume."
        gaps.append({"skill": d["skill"], "importance": d["importance"], "status": d["status"], "reason": reason})
    return {"strengths": strengths, "high_priority": high, "medium_priority": medium, "low_priority": low, "details": gaps}
