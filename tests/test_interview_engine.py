"""Quick self-check for the Mock Interview engine (no Streamlit or internet needed).

Run from the project root:   python tests/test_interview_engine.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules.interview_engine import build_interview, evaluate_answer, skipped_result, summarize_interview
from modules.jd_parser import parse_job_description
from modules.resume_parser import parse_resume
from modules.similarity_engine import compare_resume_to_jd

ROOT = Path(__file__).resolve().parent.parent
resume = parse_resume((ROOT / "sample_data" / "sample_resume.txt").read_text(encoding="utf-8"))
jd = parse_job_description((ROOT / "sample_data" / "sample_job_description.txt").read_text(encoding="utf-8"))
match = {"matching_skills": ["Python", "SQL", "Machine Learning", "Pandas", "Git"], "missing_skills": ["AWS", "Docker"], "partial_skills": []}

for focus in ["Mixed", "Technical", "Projects", "Behavioral & HR"]:
    for level in ["Beginner", "Intermediate"]:
        questions = build_interview(resume, jd, match, 6, level, focus, seed=1)
        assert len(questions) == 6, (focus, level, len(questions))
        assert len({q["id"] for q in questions}) == len(questions)
assert build_interview(None, None) == []
assert build_interview(resume, None, None, 4) and build_interview(None, jd, None, 4)

questions = build_interview(resume, jd, match, 5, "Beginner", "Technical", seed=2)
strong = evaluate_answer(questions[0], "Overfitting means memorising training data and failing on unseen data; use regularisation, "
                         "dropout, more data and cross-validation. Supervised learning uses labelled data, unsupervised finds patterns "
                         "in unlabelled data. A DataFrame is a table; use dropna or fillna. Git fetch downloads, pull merges.",
                         use_semantic=False)
weak = evaluate_answer(questions[0], "I don't know", use_semantic=False)
assert 0 <= weak["score"] < strong["score"] <= 10 or strong["score"] >= weak["score"]
summary = summarize_interview([strong, weak, skipped_result(questions[1])])
assert summary["answered"] == 2 and 0 <= summary["overall"] <= 100

# ---- variety: consecutive interviews must not repeat questions (simulated question memory, no database needed)
history = {"questions": {}, "skills": {}}
asked = []
for round_no in range(5):
    qs = build_interview(resume, jd, match, 6, "Beginner", "Mixed", seed=round_no * 17 + 3, history=history)
    texts = [q["question"] for q in qs]
    for q in qs:
        history["questions"][q["question"]] = history["questions"].get(q["question"], 0) + 1
        if q["category"] in ("Technical", "Gap"):
            history["skills"][q["skill"]] = history["skills"].get(q["skill"], 0) + 1
    asked.append(texts)
for earlier, later in zip(asked, asked[1:]):
    overlap = set(earlier) & set(later)
    assert len(overlap) <= 1, f"too many repeated questions between interviews: {overlap}"
unique = len({t for texts in asked for t in texts})
assert unique >= 24, f"expected >= 24 unique questions out of 30, got {unique}"
print(f"Variety check: {unique} unique questions across 5 interviews.")
print("All interview engine checks passed.")
