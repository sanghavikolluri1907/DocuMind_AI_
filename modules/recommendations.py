def generate_recommendations(resume, jd=None, match=None):
    out = {"Skills to Learn": [], "Profile Improvements": [], "Project Ideas": [], "Projects to Highlight": []}
    details = (match or {}).get("skill_details", [])
    if details:
        todo = [d for d in details if d["status"] == "missing" and d["importance"] == "required"] + \
               [d for d in details if d["status"] == "partial" and d["importance"] == "required"] + \
               [d for d in details if d["status"] == "missing" and d["importance"] == "preferred"]
        for d in todo[:8]:
            if d["status"] == "partial":
                out["Skills to Learn"].append(f"Strengthen {d['skill']}: you have related skills ({', '.join(d['via'])}); add a project that uses it directly.")
            else:
                tag = "required" if d["importance"] == "required" else "preferred"
                out["Skills to Learn"].append(f"Learn and practice {d['skill']} ({tag} for this job), ideally through a small hands-on project.")
    elif match:
        for s in match.get("missing_skills", [])[:8]:
            out["Skills to Learn"].append(f"Learn and practice {s}, especially through a small hands-on project.")
    if not resume["projects"]:
        out["Profile Improvements"].append("Add 1–2 technically relevant projects with your exact contribution and technologies.")
    if not resume["certifications"]:
        out["Profile Improvements"].append("Add relevant certifications only when they represent genuine learning.")
    if not resume["experience"]:
        out["Profile Improvements"].append("Consider internships, hackathons, open-source contributions, or substantial academic projects.")
    for d in details:
        if d["status"] == "matched" and not d["projects"] and d["importance"] == "required":
            out["Profile Improvements"].append(f"{d['skill']} is only listed in your skills section: mention it in a project bullet to prove it.")
    if match and match.get("missing_skills"):
        skills = ", ".join(match["missing_skills"][:3])
        out["Project Ideas"].append(f"Build a small project combining your current strengths with {skills}.")
    for p in (match or {}).get("project_matches", [])[:3]:
        if p["label"] != "Low":
            out["Projects to Highlight"].append(f"{p['name']} ({p['label']} relevance, {p['relevance']}/100): put it first and mention {', '.join(p['matched_skills'][:4]) or 'its key technologies'}.")
    weak = [p for p in (match or {}).get("project_matches", []) if p["label"] == "Low"]
    if weak and match.get("missing_skills"):
        out["Project Ideas"].append(f"Extend \"{weak[0]['name']}\" with {match['missing_skills'][0]} to make it relevant to this job.")
    out = {k: v for k, v in out.items() if v}
    if not out:
        out["Profile Improvements"] = ["Your profile has a solid baseline. Focus on measurable project outcomes and targeted practice."]
    return out
