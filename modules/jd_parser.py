"""Job-description parser: section-aware, so Required / Preferred skills are told apart correctly."""
import re

from .skill_extractor import extract_skills, parse_skill_list

_REQUIRED = {"required skills", "required qualifications", "requirements", "key requirements", "must have", "must haves",
             "mandatory skills", "qualifications", "minimum qualifications", "basic qualifications", "skills required",
             "technical skills", "skills", "what you need", "what we are looking for", "what you will need",
             "what you'll need", "you have", "who you are", "required", "key skills", "skill set", "tech stack"}
_PREFERRED = {"preferred skills", "preferred qualifications", "preferred", "nice to have", "nice to haves", "good to have",
              "bonus", "bonus points", "desirable", "desired skills", "plus", "a plus", "optional", "additional skills",
              "extra credit", "preferred requirements", "good to have skills"}
_RESPONSIBILITIES = {"responsibilities", "key responsibilities", "duties", "what you will do", "what you'll do", "role",
                     "the role", "job description", "your role", "day to day", "roles and responsibilities",
                     "role and responsibilities", "what you will be doing"}
_EDUCATION = {"education", "educational qualification", "educational qualifications", "education requirements",
              "education and experience", "academic requirements", "eligibility"}
_OTHER = {"about us", "about the company", "about the role", "benefits", "perks", "what we offer", "location", "salary",
          "how to apply", "company", "overview", "about", "why join us", "equal opportunity"}
_KIND = {**{h: "required" for h in _REQUIRED}, **{h: "preferred" for h in _PREFERRED},
         **{h: "responsibilities" for h in _RESPONSIBILITIES}, **{h: "education" for h in _EDUCATION},
         **{h: "other" for h in _OTHER}}

_PREF_CUE = re.compile(r"\b(?:preferred|nice to have|good to have|a plus|is a plus|are a plus|\(plus\)|bonus|desirable|"
                       r"optional|an advantage|advantageous|added advantage|not mandatory)\b", re.I)
_BULLET = re.compile(r"^\s*(?:[•●▪■◦○➢➤►▶✓✔*·]\s*|[-–—]\s+|\d{1,2}[.)]\s+)")


def _clean(line: str) -> str:
    return _BULLET.sub("", line.replace("\u00a0", " ").replace("’", "'")).strip()


def _heading(line: str):
    """(kind, inline_rest) when `line` is a section heading such as 'Required Skills:' or 'Preferred: Docker'."""
    s = line.replace("’", "'").strip()
    plain = re.sub(r"[^a-z' &/]", "", s.lower()).strip()
    if plain in _KIND and len(s.split()) <= 5 and (not s.endswith(".")):
        return _KIND[plain], ""
    m = re.match(r"^\W*([A-Za-z' &/]{3,32}?)\s*[:\-–—]\s*(.+)$", s)
    if m:
        key = m.group(1).lower().strip()
        if key in _KIND and key not in {"role", "about", "company", "location", "plus", "skills", "required", "preferred"} or \
                key in {"skills", "required", "preferred", "plus"} and len(m.group(2).split()) <= 40:
            return _KIND[key], m.group(2).strip()
    return None


def parse_job_description(text: str) -> dict:
    text = text.replace("\r", "\n").replace("\u00a0", " ")
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    section = None
    explicit_required = False
    req, pref, mention = set(), set(), set()
    responsibilities, education_lines, other_lines = [], [], []

    for raw in lines:
        head = _heading(raw)
        content = raw
        if head:
            section, content = head[0], head[1]
            explicit_required = explicit_required or section == "required"
            if not content:
                continue
        line = _clean(content)
        if not line:
            continue
        if section == "education":
            education_lines.append(line)
            continue
        if section == "responsibilities":
            responsibilities.append(line)
        elif section is None or section == "other":
            other_lines.append(line)
        is_list_section = section in ("required", "preferred")
        for clause in re.split(r"(?<=[.!?;])\s+", line):  # "Docker is nice to have." must not demote the other skills
            clause = clause.strip()
            if not clause:
                continue
            use_list = is_list_section and (head is not None or len(clause.split()) <= 12)
            skills = set(parse_skill_list(clause) if use_list else extract_skills(clause))
            if not skills:
                continue
            if section == "preferred" or _PREF_CUE.search(clause):
                pref |= skills
            elif section == "required":
                req |= skills
            else:
                mention |= skills

    if explicit_required or req:
        required = set(req)
        preferred = (pref | mention) - required      # skills only named in duties are treated as nice-to-have
    else:  # no "Required" section at all: everything that is not marked optional is required
        required = set(mention) | (set(req))
        preferred = pref - required
    all_skills = sorted(required | preferred)

    lower = text.lower()
    experience = re.findall(r"\b\d+\s*(?:\+|-\s*\d+)?\s*(?:years?|yrs?)\b", text, re.I)
    education_terms = []
    for pattern, label in [(r"\bbachelor'?s?\b", "Bachelor"), (r"\bmaster'?s?\b", "Master"), (r"\bb\.?\s?tech\b", "B.Tech"),
                           (r"\bb\.e\b|\bbe\s+in\b", "B.E"), (r"\bcomputer science\b", "Computer Science"),
                           (r"\bengineering\b", "Engineering"), (r"\bphd\b|\bdoctorate\b", "PhD")]:
        if re.search(pattern, lower):
            education_terms.append(label)

    if not responsibilities:
        responsibilities = [_clean(l) for l in other_lines if len(_clean(l)) > 35]
    title = next((_clean(l) for l in lines if not _heading(l) and len(l.split()) <= 8), "")
    return {
        "job_title": title,
        "required_skills": sorted(required),
        "preferred_skills": sorted(preferred),
        "all_skills": all_skills,
        "experience_requirements": sorted(set(e.strip() for e in experience)),
        "education_requirements": sorted(set(education_terms)),
        "responsibilities": responsibilities[:12],
    }
