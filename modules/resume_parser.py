"""Resume parser: line-based section detection and project grouping (one project = one entry, however many lines)."""
import re

from .skill_extractor import extract_skills, parse_skill_list

_SECTIONS = {
    "skills": {"skills", "technical skills", "core competencies", "key skills", "skill set", "technologies", "tech stack",
               "technical proficiency", "areas of expertise", "tools and technologies", "tools & technologies",
               "technical expertise", "skills & tools", "skills and tools"},
    "projects": {"projects", "academic projects", "personal projects", "key projects", "project work", "project experience",
                 "major projects", "mini projects", "notable projects", "selected projects", "projects undertaken"},
    "education": {"education", "academic background", "academic qualifications", "educational qualifications",
                  "education and qualifications", "academics", "educational background"},
    "experience": {"experience", "work experience", "professional experience", "employment", "internship", "internships",
                   "internship experience", "work history", "employment history", "industrial experience", "training"},
    "certifications": {"certifications", "certificates", "certification", "licenses & certifications",
                       "licenses and certifications", "courses", "courses and certifications", "online courses"},
    "other": {"summary", "professional summary", "career objective", "objective", "profile", "about me", "achievements",
              "awards", "honors", "languages", "hobbies", "interests", "declaration", "references", "publications",
              "extracurricular", "extracurricular activities", "activities", "personal details", "links", "contact",
              "positions of responsibility", "volunteering", "co-curricular activities"},
}
_KIND = {name: sec for sec, names in _SECTIONS.items() for name in names}
_INLINE_OK = {"skills", "projects", "education", "experience", "certifications"}

_BULLET_SYM = re.compile(r"^\s*[•●▪■◦○➢➤►▶✓✔*·]\s*")
_BULLET_DASH = re.compile(r"^\s*(?:[-–—]|\d{1,2}[.)])\s+")
_TITLE_SEP = re.compile(r"\s[-–—|]\s|:\s")
_META = re.compile(r"^(?:tech(?:nologies|nology)?(?: used| stack)?|tools?(?: used| & technologies| and technologies)?|(?:tech )?stack|duration|date|link|github|role|description|"
                   r"environment|team size|period|domain|features?|key features|outcome|result|responsibilit(?:y|ies))\s*[:\-–]", re.I)
_DATE = re.compile(r"^\(?(?:\d{4}|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4})", re.I)
_ACTION = re.compile(r"^(?:built|build|developed|designed|created|implemented|used|uses|use|using|worked|analy[sz]ed|automated|"
                     r"trained|deployed|integrated|performed|managed|led|collaborated|engineered|a|an|the|this|it|to|made|"
                     r"proposed|conducted|applied|utili[sz]ed|leveraged|achieved|added|enhanced|optimi[sz]ed|improved|"
                     r"collected|tested|wrote|handled|include[sd]?|features?|supports?|allows?|enables?|provides?|"
                     r"helps?|generates?|predicts?|detects?|classif(?:y|ies|ied)|extracts?|stores?|tracks?|"
                     r"fetch(?:es|ed)?|connected|focused|aimed|responsible|contributed|reduced|increased|"
                     r"launched|maintained|migrated|configured|set up|setup|visuali[sz]ed|scraped|crawled|"
                     r"experimented|researched|presented|published|won|ranked|secured)\b", re.I)
_URL_LINE = re.compile(r"^(?:https?://|www\.|github\.com|gitlab\.com|\S+\.(?:com|io|app|dev|in)/)", re.I)
_MONTH = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"
_DATE_TAIL = re.compile(
    r"(?:\s*[|,(\[]\s*|\s{2,}|\s+)"
    r"(?P<d>(?:" + _MONTH + r"\s+)?\d{4}(?:\s*(?:[-–—]|to)\s*(?:(?:" + _MONTH + r"\s+)?\d{4}|present|ongoing|current|till date))?"
    r"|(?:" + _MONTH + r"\s+)?\d{4}\s*[-–—]\s*(?:present|ongoing|current))\s*[)\]]?\s*$", re.I)
_STOP = {"and", "of", "the", "for", "in", "on", "to", "a", "an", "with", "using", "by", "from", "via", "at", "or", "&", "-", "–", "—", "|"}
_TERMINAL = (".", "!", "?", ":")
_JOINERS = (",", "-", "–", "&", "(", "/")
_JOIN_WORDS = {"and", "with", "using", "for", "to", "of", "in", "on", "by", "the", "a", "an", "or", "that", "which", "from", "as"}


def _normalize(text: str) -> str:
    text = text.replace("\r", "\n").replace("\u00a0", " ").replace("\u2022", "•").replace("\t", "  ")
    return re.sub(r"[ ]{3,}(?=\S)", "  ", text)


def _heading(line: str):
    """(section, inline_rest) if `line` is a section heading, else None."""
    s = line.strip()
    if not s or len(s.split()) > 6:
        return None
    plain = re.sub(r"[^a-z&' ]", " ", s.lower())
    plain = re.sub(r"\s+", " ", plain).strip()
    if plain in _KIND and not s.endswith("."):
        return _KIND[plain], ""
    m = re.match(r"^([A-Za-z&' ]{3,32}?)\s*:\s*(.+)$", s)
    if m:
        key = re.sub(r"\s+", " ", m.group(1).lower()).strip()
        if _KIND.get(key) in _INLINE_OK:
            return _KIND[key], m.group(2).strip()
    return None


def _split_sections(text: str) -> tuple[list[str], dict[str, list[str]]]:
    header, sections, current = [], {k: [] for k in _SECTIONS}, None
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        head = _heading(line)
        if head:
            current = head[0]
            if head[1]:
                sections[current].append(head[1])
            continue
        (sections[current] if current else header).append(line)
    return header, sections


def _bullet(line: str) -> tuple[bool, str]:
    m = _BULLET_SYM.match(line) or _BULLET_DASH.match(line)
    return (True, line[m.end():].strip()) if m else (False, line.strip())


def _cap_ratio(t: str) -> float:
    """Share of content words that start with a capital letter or digit (Title Case ~ 1.0, a sentence ~ low)."""
    words = [w for w in re.findall(r"[A-Za-z0-9][\w.+#/&'-]*", t) if w.lower() not in _STOP]
    if not words:
        return 0.0
    return sum(1 for w in words if w[0].isupper() or w[0].isdigit()) / len(words)


def _is_desc_start(t: str) -> bool:
    return bool(_META.match(t) or _URL_LINE.match(t) or _ACTION.match(t) or t[:1].islower())


def _looks_like_title(t: str) -> bool:
    """A project/role title: short, Title-Case (or 'Name - details'), not a sentence, not a metadata line."""
    t = t.strip()
    if not t or _is_desc_start(t):
        return False
    m = _TITLE_SEP.search(t)
    if m and len(t[:m.start()].split()) <= 9 and _cap_ratio(t[:m.start()]) >= 0.6:
        return True
    if _DATE_TAIL.search(t) and len(t.split()) <= 14:
        return True
    return len(t.split()) <= 10 and not t.endswith(_TERMINAL) and _cap_ratio(t) >= 0.8


def _prev_text(entry: dict) -> str:
    return entry["body"][-1] if entry["body"] else entry["head"]


def _unwrap(items: list[tuple[bool, str]]) -> list[tuple[bool, str]]:
    """Glue lines that a PDF / editor wrapped back together, so one wrapped line is never counted as a new project."""
    out: list[tuple[bool, str]] = []
    for is_b, t in items:
        if not t:
            continue
        if out and not is_b:
            pb, prev = out[-1]
            words = prev.split()
            last = words[-1].lower() if words else ""
            wrapped = (
                t[:1].islower()
                or prev.rstrip().endswith(_JOINERS) or last in _JOIN_WORDS
                or (len(words) >= 6 and not prev.rstrip().endswith(_TERMINAL) and len(t.split()) == 1
                    and not _META.match(t) and not _DATE.match(t))                      # "...Machine" / "Learning"
                or (len(words) >= 7 and not prev.rstrip().endswith(_TERMINAL) and _cap_ratio(prev) < 0.8
                    and not _looks_like_title(t) and not _is_desc_start(t) and not _DATE.match(t))  # mid-sentence break
            )
            if wrapped and not _META.match(t) and not _URL_LINE.match(t):
                out[-1] = (pb, prev.rstrip() + " " + t)
                continue
        out.append((is_b, t))
    return out


def _has_desc(entry: dict) -> bool:
    return any(not (_META.match(b) or _URL_LINE.match(b) or _DATE.match(b)) for b in entry["body"])


def _title_only(entry: dict) -> bool:
    h = entry["head"]
    return (not entry["body"] and not _TITLE_SEP.search(h) and len(h.split()) <= 10 and not h.endswith(_TERMINAL))


def group_entries(lines: list[str]) -> list[dict]:
    """Group raw lines into entries: {"head": first line, "body": [following lines]} - one entry per project/role.

    A new entry starts only on a line that *looks like a title*; everything else (bullets, descriptions,
    Technologies:/GitHub: lines, dates, wrapped text) is attached to the entry above it."""
    items = _unwrap([_bullet(l) for l in lines if l.strip()])
    has_titles = any(not b for b, _ in items)
    entries: list[dict] = []
    for is_b, t in items:
        if not entries:
            entries.append({"head": t, "body": []})
            continue
        cur = entries[-1]
        prev = _prev_text(cur)
        if is_b:
            sep = _TITLE_SEP.search(t)
            if has_titles or not (sep and len(t[:sep.start()].split()) <= 9):
                cur["body"].append(t)                       # bullet under a project title
            else:
                entries.append({"head": t, "body": []})     # "• Name - description" list: one project per bullet
        elif _META.match(t) or _URL_LINE.match(t) or (_DATE.match(t) and len(t.split()) <= 8):
            cur["body"].append(t)
        elif _is_desc_start(t):
            cur["body"].append(t)                           # starts like a sentence: belongs to the project above
        elif cur["body"] and not _has_desc(cur) and not (_TITLE_SEP.search(t) or _DATE_TAIL.search(t)):
            cur["body"].append(t)                           # only GitHub:/Tech: lines so far - this is its description
        elif _looks_like_title(t):
            entries.append({"head": t, "body": []})
        elif _title_only(cur) or not prev.rstrip().endswith(_TERMINAL):
            cur["body"].append(t)                           # short description / unfinished sentence under a title
        elif len(t.split()) <= 10 and not t.endswith(_TERMINAL):
            entries.append({"head": t, "body": []})         # finished sentence above, new un-capitalised title below
        else:
            cur["body"].append(t)
    return entries


def _split_head(head: str) -> tuple[str, str]:
    """Project title and the rest of the first line ('DocuMind AI | Python | 2024' -> 'DocuMind AI', 'Python | 2024')."""
    dm = _DATE_TAIL.search(head)
    duration = ""
    if dm and dm.start() > 2:                       # "E-Commerce Website   Jan 2024 - Mar 2024" -> title + duration
        duration, head = dm.group("d").strip(), head[:dm.start()].strip(" |,-–—")
    name, rest = _split_head_core(head)
    return name, (f"Duration: {duration}. {rest}".strip() if duration else rest)


def _split_head_core(head: str) -> tuple[str, str]:
    m = re.match(r"^(.{2,80}?)\s[-–—|]\s(.*)$", head) or re.match(r"^([^:]{2,60}?):\s+(.*)$", head)
    if m and len(m.group(1).split()) <= 10:
        name, rest = m.group(1), m.group(2)
    elif len(head.split()) <= 10 and not head.endswith("."):
        name, rest = head, ""
    else:
        words = head.split()
        name, rest = " ".join(words[:6]), head
    par = re.search(r"\(([^)]*)\)\s*$", name)
    if par:
        rest = f"Technologies: {par.group(1)}. {rest}".strip()
        name = name[:par.start()].strip()
    return name.strip(" -–—|:•"), rest.strip()


def parse_projects(lines: list[str], limit: int = 12) -> list[dict]:
    details = []
    for e in group_entries(lines):
        name, rest = _split_head(e["head"])
        description = " ".join(x for x in [rest] + e["body"] if x).strip()
        if len((name + " " + description).split()) < 3:
            continue
        text = f"{name} - {description}" if description else name
        details.append({"name": name, "description": description, "text": text, "skills": extract_skills(text)})
    return details[:limit]


def _items(lines: list[str], min_len: int, limit: int = 10) -> list[str]:
    out = []
    for e in group_entries(lines):
        text = " ".join([e["head"]] + e["body"]).strip(" •-\t")
        if len(text) > min_len:
            out.append(text)
    return out[:limit]


def _name(header: list[str]) -> str:
    for l in header:
        if re.search(r"@|https?://|www\.|linkedin|github\.com|\d{6,}", l):
            continue
        if len(l.split()) <= 6 and not re.search(r"[:|]", l):
            return l.strip(" •-")
    return "Unknown"


def parse_resume(text: str) -> dict:
    text = _normalize(text)
    header, sec = _split_sections(text)
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    phone = re.search(r"(?:\+91[-\s]?)?[6-9]\d{9}", text) or re.search(r"\+?\d[\d\s().-]{8,15}\d", text)

    project_details = parse_projects(sec["projects"])
    certifications = [x for x in (_bullet(l)[1] for l in sec["certifications"]) if len(x) > 5][:10]
    education = _items(sec["education"], 10)
    experience = _items(sec["experience"], 10)

    listed = set()
    for l in sec["skills"]:
        listed |= set(parse_skill_list(_bullet(l)[1]))
    # a degree title such as "B.Tech in AI and Machine Learning" is not a claim of skill, so education lines are skipped
    skill_text = "\n".join(l for l in text.split("\n") if l.strip() not in set(sec["education"])) if sec["education"] else text
    skills = sorted(set(extract_skills(skill_text)) | listed)

    evidence = {}
    exp_text = " ".join(sec["experience"])
    for s in skills:
        in_projects = [p["name"] for p in project_details if s in p["skills"]]
        evidence[s] = {"listed": s in listed, "projects": in_projects,
                       "experience": s in extract_skills(exp_text) if exp_text else False}
    return {
        "name": _name(header), "email": email.group(0) if email else "",
        "phone": phone.group(0).strip() if phone else "", "skills": skills,
        "education": education, "projects": [p["text"] for p in project_details],
        "project_details": project_details, "certifications": certifications,
        "experience": experience, "skill_evidence": evidence,
    }
