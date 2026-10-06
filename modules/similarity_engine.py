"""Resume <-> job matching.

Score = skill coverage (required skills weigh far more than preferred ones)
      + semantic similarity of the whole profile to the job
      + how relevant the BEST INDIVIDUAL PROJECTS are (every project is scored on its own).

Semantic similarity uses sentence embeddings (all-MiniLM-L6-v2) when available and falls back to TF-IDF cosine
similarity, so the match still works offline or when the model cannot be downloaded.
"""
import re

from .skill_extractor import match_skill

_MODEL = None          # loaded SentenceTransformer, or False when unavailable
_MODEL_NAME = "all-MiniLM-L6-v2"


def _get_model():
    global _MODEL
    if _MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            _MODEL = SentenceTransformer(_MODEL_NAME)
        except Exception:
            _MODEL = False
    return _MODEL or None


def _cosines(texts: list[str], queries: list[str]):
    """Matrix [len(texts) x len(queries)] of cosine similarities and the method used."""
    model = _get_model()
    if model is not None:
        try:
            a = model.encode(texts, normalize_embeddings=True)
            b = model.encode(queries, normalize_embeddings=True)
            return a @ b.T, "embeddings"
        except Exception:
            pass
    from sklearn.feature_extraction.text import TfidfVectorizer
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True).fit(texts + queries)
    a, b = vec.transform(texts), vec.transform(queries)
    return (a @ b.T).toarray(), "tfidf"


def _calibrate(cos: float, method: str) -> float:
    """Raw cosine -> 0..1. Unrelated text already scores ~0.1-0.2 with MiniLM, so the scale is stretched."""
    lo, hi = (0.15, 0.60) if method == "embeddings" else (0.02, 0.30)
    return max(0.0, min(1.0, (cos - lo) / (hi - lo)))


def _status_details(jd_skills: list[tuple[str, str]], resume: dict) -> list[dict]:
    have = set(resume.get("skills", []))
    evidence = resume.get("skill_evidence", {})
    details = []
    for skill, importance in jd_skills:
        status, via = match_skill(skill, have)
        projects = []
        for v in via:
            projects += evidence.get(v, {}).get("projects", [])
        projects = list(dict.fromkeys(projects))
        if status == "missing":
            note = "Not found on the resume."
        else:
            how = f"listed on resume" if via == [skill] else f"via {', '.join(via)}"
            note = ("Matched" if status == "matched" else "Related skill") + f" ({how})"
            note += f"; used in: {', '.join(projects)}" if projects else "; not shown in any project"
        details.append({"skill": skill, "importance": importance, "status": status, "via": via,
                        "projects": projects, "note": note})
    return details


def _coverage(details: list[dict], importance: str):
    items = [d for d in details if d["importance"] == importance]
    if not items:
        return None
    return sum(1.0 if d["status"] == "matched" else 0.5 if d["status"] == "partial" else 0.0 for d in items) / len(items)


def _project_matches(resume: dict, jd: dict, jd_skills: list[tuple[str, str]], queries: list[str]) -> tuple[list[dict], str]:
    projects = resume.get("project_details") or [{"name": p.split(" - ")[0][:60], "text": p, "skills": []}
                                                  for p in resume.get("projects", [])]
    if not projects or not queries:
        return [], "none"
    sims, method = _cosines([p["text"] for p in projects], queries)
    denom = max(1, min(len(jd_skills), 3))  # one project cannot be expected to show every skill: 3 job skills = full overlap
    results = []
    for i, p in enumerate(projects):
        pset = set(p.get("skills", []))
        matched, partial = [], []
        for skill, _ in jd_skills:
            status, via = match_skill(skill, pset)
            (matched if status == "matched" else partial if status == "partial" else []).append(skill)
        overlap = min(1.0, (len(matched) + 0.5 * len(partial)) / denom)
        semantic = _calibrate(float(sims[i].max()), method)
        relevance = round(100 * (0.6 * overlap + 0.4 * semantic))
        label = "Strong" if relevance >= 55 else "Moderate" if relevance >= 30 else "Low"
        results.append({"name": p["name"], "description": p.get("description", ""), "relevance": relevance, "label": label,
                        "matched_skills": matched, "partial_skills": partial, "technologies": sorted(pset),
                        "semantic": round(semantic * 100)})
    results.sort(key=lambda r: r["relevance"], reverse=True)
    return results, method


def compare_resume_to_jd(resume: dict, jd: dict) -> dict:
    required = list(jd.get("required_skills") or [])
    preferred = [s for s in jd.get("preferred_skills", []) if s not in required]
    if not required and not preferred:
        required = list(jd.get("all_skills", []))
    jd_skills = [(s, "required") for s in required] + [(s, "preferred") for s in preferred]
    details = _status_details(jd_skills, resume)

    req_cov, pref_cov = _coverage(details, "required"), _coverage(details, "preferred")
    if req_cov is not None and pref_cov is not None:
        skills_score = 0.85 * req_cov + 0.15 * pref_cov
    else:
        skills_score = req_cov if req_cov is not None else pref_cov

    # ---- semantic part: whole profile vs the job, and each project vs the job's duties / skills
    queries = [r for r in jd.get("responsibilities", []) if len(r.split()) >= 3]
    if jd_skills:
        queries.append((jd.get("job_title", "") + " requires " + ", ".join(s for s, _ in jd_skills)).strip())
    profile = " ".join([", ".join(resume.get("skills", []))] + resume.get("projects", []) + resume.get("experience", []))
    jd_doc = " ".join([jd.get("job_title", "")] + [s for s, _ in jd_skills] + jd.get("responsibilities", [])).strip()
    semantic = None
    method = "none"
    if profile.strip() and jd_doc:
        sims, method = _cosines([profile], [jd_doc])
        semantic = _calibrate(float(sims[0][0]), method)
    project_results, pmethod = _project_matches(resume, jd, jd_skills, queries)
    top = [p["relevance"] / 100 for p in project_results[:2]]
    project_score = sum(top) / len(top) if top else None

    parts = []   # (weight, value)
    if skills_score is not None:
        parts.append((0.70, skills_score))
    if semantic is not None:
        parts.append((0.15 if project_score is not None else 0.30, semantic))
    if project_score is not None:
        parts.append((0.15, project_score))
    total_w = sum(w for w, _ in parts)
    score = round(100 * sum(w * v for w, v in parts) / total_w) if total_w else 0

    def names(status):
        order = sorted((d for d in details if d["status"] == status), key=lambda d: d["importance"] != "required")
        return [d["skill"] for d in order]

    notes = []
    if not jd_skills:
        notes.append("No recognisable skills were found in the job description, so this score uses text similarity only (low confidence).")
    unproven = [d["skill"] for d in details if d["status"] == "matched" and not d["projects"]]
    if unproven:
        notes.append("Listed but not shown in any project: " + ", ".join(unproven[:6]) + ". Showing them inside a project makes them more convincing.")
    label = "sentence embeddings (all-MiniLM-L6-v2)" if "embeddings" in (method, pmethod) else "TF-IDF text similarity (offline fallback)"
    explanation = ("Score = 70% skill coverage (required skills count most, preferred skills 15% of that part), "
                   "15% overall semantic similarity and 15% relevance of your best two projects, each project scored on its own. "
                   f"Semantic method: {label}. ") + " ".join(notes)
    return {
        "match_percentage": max(0, min(100, score)),
        "matching_skills": names("matched"),
        "missing_skills": names("missing"),
        "partial_skills": names("partial"),
        "required_coverage": None if req_cov is None else round(req_cov * 100),
        "preferred_coverage": None if pref_cov is None else round(pref_cov * 100),
        "semantic_similarity": None if semantic is None else round(semantic * 100, 2),
        "semantic_method": label,
        "skill_details": details,
        "project_matches": project_results,
        "explanation": explanation.strip(),
    }
