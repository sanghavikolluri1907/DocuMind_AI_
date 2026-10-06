"""Skill vocabulary, skill extraction and skill-to-skill matching rules.

* ``extract_skills(text)``     -> canonical skills found anywhere in a text (dictionary based, word-boundary safe).
* ``parse_skill_list(text)``   -> same, plus short unknown items from an explicit list such as "Skills: Python, Kafka".
* ``match_skill(skill, have)`` -> ("matched" | "partial" | "missing", [evidence skills]) using explicit rules:
      MySQL counts as SQL, TensorFlow counts as Machine Learning, AWS is only *partial* credit for Azure, etc.
"""
import re

SKILL_ALIASES = {
    # languages
    "python": "Python", "python3": "Python", "java": "Java", "c++": "C++", "c#": "C#", "golang": "Go",
    "javascript": "JavaScript", "js": "JavaScript", "typescript": "TypeScript", "kotlin": "Kotlin", "php": "PHP",
    "ruby": "Ruby", "scala": "Scala", "bash": "Bash", "shell scripting": "Bash", "matlab": "MATLAB",
    # web
    "html": "HTML", "html5": "HTML", "css": "CSS", "css3": "CSS", "react": "React", "react.js": "React", "reactjs": "React",
    "angular": "Angular", "vue": "Vue", "vue.js": "Vue", "node.js": "Node.js", "nodejs": "Node.js", "node": "Node.js",
    "express": "Express", "express.js": "Express", "bootstrap": "Bootstrap", "tailwind": "Tailwind CSS", "tailwind css": "Tailwind CSS",
    "django": "Django", "flask": "Flask", "fastapi": "FastAPI", "streamlit": "Streamlit", "spring boot": "Spring Boot", "spring": "Spring Boot",
    "rest api": "REST API", "rest apis": "REST API", "restful api": "REST API", "restful apis": "REST API", "restful": "REST API",
    "api": "API", "apis": "API", "graphql": "GraphQL",
    # data / databases
    "sql": "SQL", "mysql": "MySQL", "postgresql": "PostgreSQL", "postgres": "PostgreSQL", "sqlite": "SQLite",
    "sql server": "SQL Server", "mssql": "SQL Server", "oracle": "Oracle", "mongodb": "MongoDB", "nosql": "NoSQL",
    "redis": "Redis", "firebase": "Firebase", "pandas": "Pandas", "numpy": "NumPy", "matplotlib": "Matplotlib",
    "seaborn": "Seaborn", "plotly": "Plotly", "excel": "Excel", "ms excel": "Excel", "microsoft excel": "Excel",
    "power bi": "Power BI", "powerbi": "Power BI", "tableau": "Tableau", "data analysis": "Data Analysis",
    "data analytics": "Data Analysis", "data science": "Data Science", "data visualization": "Data Visualization",
    "data visualisation": "Data Visualization", "statistics": "Statistics", "etl": "ETL", "big data": "Big Data",
    "hadoop": "Hadoop", "apache spark": "Spark", "pyspark": "Spark", "spark": "Spark", "airflow": "Airflow",
    # ML / AI
    "machine learning": "Machine Learning", "ml": "Machine Learning", "deep learning": "Deep Learning",
    "scikit-learn": "scikit-learn", "scikit learn": "scikit-learn", "sklearn": "scikit-learn",
    "tensorflow": "TensorFlow", "pytorch": "PyTorch", "keras": "Keras", "nlp": "NLP",
    "natural language processing": "NLP", "nltk": "NLTK", "spacy": "spaCy", "computer vision": "Computer Vision",
    "opencv": "OpenCV", "generative ai": "Generative AI", "gen ai": "Generative AI", "genai": "Generative AI",
    "llm": "LLM", "llms": "LLM", "large language models": "LLM", "large language model": "LLM", "rag": "RAG",
    "langchain": "LangChain", "hugging face": "Hugging Face", "huggingface": "Hugging Face", "transformers": "Transformers",
    "bert": "BERT", "mlops": "MLOps",
    # tools / cloud / process
    "git": "Git", "github": "GitHub", "gitlab": "GitLab", "docker": "Docker", "kubernetes": "Kubernetes", "k8s": "Kubernetes",
    "aws": "AWS", "amazon web services": "AWS", "azure": "Azure", "gcp": "GCP", "google cloud": "GCP",
    "cloud computing": "Cloud Computing", "linux": "Linux", "jenkins": "Jenkins", "github actions": "GitHub Actions",
    "ci/cd": "CI/CD", "jira": "Jira", "postman": "Postman", "figma": "Figma", "selenium": "Selenium", "pytest": "Pytest",
    "agile": "Agile", "scrum": "Agile",
    # computer-science fundamentals
    "data structures": "Data Structures", "dsa": "Data Structures", "algorithms": "Algorithms", "oop": "OOP",
    "oops": "OOP", "object oriented programming": "OOP", "object-oriented programming": "OOP", "object oriented": "OOP",
}

# canonical skill -> resume skills that FULLY demonstrate it (knowing MySQL means you know SQL)
IMPLIED_BY = {
    "SQL": {"MySQL", "PostgreSQL", "SQLite", "SQL Server", "Oracle"},
    "Git": {"GitHub", "GitLab"},
    "Python": {"Pandas", "NumPy", "Flask", "Django", "FastAPI", "Streamlit", "scikit-learn", "Matplotlib", "Seaborn"},
    "JavaScript": {"TypeScript", "Node.js", "Express"},
    "CSS": {"Bootstrap", "Tailwind CSS"},
    "REST API": set(),
    "API": {"REST API", "GraphQL"},
    "NoSQL": {"MongoDB", "Redis", "Firebase"},
    "Machine Learning": {"scikit-learn", "TensorFlow", "PyTorch", "Keras", "Deep Learning", "MLOps"},
    "Deep Learning": {"TensorFlow", "PyTorch", "Keras"},
    "NLP": {"NLTK", "spaCy", "Transformers", "BERT", "Hugging Face"},
    "Computer Vision": {"OpenCV"},
    "Generative AI": {"LLM", "RAG", "LangChain"},
    "LLM": {"LangChain", "RAG"},
    "Cloud Computing": {"AWS", "Azure", "GCP"},
    "CI/CD": {"Jenkins", "GitHub Actions"},
    "Data Visualization": {"Matplotlib", "Seaborn", "Plotly", "Power BI", "Tableau"},
    "Spark": set(),
}

# canonical skill -> resume skills that give PARTIAL credit (related, not the same thing)
RELATED_TO = {
    "Data Analysis": {"Pandas", "NumPy", "Excel", "Power BI", "Tableau", "Data Science", "SQL", "Matplotlib", "Seaborn"},
    "Data Science": {"Machine Learning", "Data Analysis", "Pandas", "scikit-learn"},
    "Statistics": {"Data Science", "Machine Learning", "Data Analysis"},
    "Machine Learning": {"NLP", "Computer Vision", "Generative AI", "LLM", "Data Science"},
    "Deep Learning": {"NLP", "Computer Vision", "Machine Learning"},
    "NLP": {"Machine Learning", "LLM", "Generative AI"},
    "Computer Vision": {"Deep Learning", "Machine Learning"},
    "Generative AI": {"NLP", "Deep Learning"},
    "LLM": {"Generative AI", "NLP"},
    "REST API": {"Flask", "FastAPI", "Django", "Express", "Spring Boot", "API"},
    "API": {"Flask", "FastAPI", "Django", "Express", "Spring Boot"},
    "JavaScript": {"React", "Angular", "Vue"},
    "React": {"JavaScript", "Angular", "Vue"},
    "Angular": {"JavaScript", "React", "Vue"},
    "Vue": {"JavaScript", "React", "Angular"},
    "HTML": {"React", "Angular", "Vue"},
    "AWS": {"Azure", "GCP", "Cloud Computing"},
    "Azure": {"AWS", "GCP", "Cloud Computing"},
    "GCP": {"AWS", "Azure", "Cloud Computing"},
    "Cloud Computing": set(),
    "Docker": {"Kubernetes"},
    "Kubernetes": {"Docker"},
    "MySQL": {"PostgreSQL", "SQL Server", "SQLite", "Oracle", "SQL"},
    "PostgreSQL": {"MySQL", "SQL Server", "SQLite", "Oracle", "SQL"},
    "SQL Server": {"MySQL", "PostgreSQL", "SQLite", "Oracle", "SQL"},
    "SQLite": {"MySQL", "PostgreSQL", "SQL Server", "Oracle", "SQL"},
    "Oracle": {"MySQL", "PostgreSQL", "SQL Server", "SQLite", "SQL"},
    "MongoDB": {"NoSQL", "Redis", "Firebase"},
    "OOP": {"Java", "C++", "C#", "Python", "Kotlin"},
    "Big Data": {"Spark", "Hadoop"},
    "ETL": {"Airflow", "Spark", "SQL"},
    "Agile": {"Jira"},
    "Excel": {"Power BI", "Tableau"},
    "Data Structures": {"Algorithms"},
    "Algorithms": {"Data Structures"},
    "MLOps": {"Docker", "Machine Learning"},
    "Tensorflow": set(),
}

# words that look like list items but are not hard skills (kept out of the "unknown skill" extras)
_NOT_SKILLS = re.compile(
    r"^(?:strong|good|excellent|solid|proven|ability|able|experience|knowledge|understanding|familiarity|exposure|"
    r"bachelor|master|degree|b\.?tech|b\.?e\b|m\.?tech|phd|and|or|with|in|the|a|an|of|to|must|should|nice|plus|"
    r"preferred|required|minimum|years?|communication|teamwork|team|leadership|problem|analytical|critical|"
    r"interpersonal|self|time|attention|willing|passion|eager|fresher|freshers|candidates?|etc)\b", re.I)
_BAD_ITEM = re.compile(r"(?:year|degree|bachelor|master|certif|salary|location|remote|onsite|full[- ]?time|intern\b|"
                       r"skills?\b|experience|ability|responsib|requirement)", re.I)

_ALIAS_RE = {a: re.compile(r"(?<![\w+#.])" + re.escape(a) + r"(?![\w+#]|\.\w)", re.I) for a in SKILL_ALIASES}
_LOWER_CANON = {}
for _c in set(SKILL_ALIASES.values()):
    _LOWER_CANON[_c.lower()] = _c


def _norm(x: str) -> str:
    return re.sub(r"[^a-z0-9+#.]+", " ", x.lower()).strip()


def canonical(name: str) -> str:
    """Canonical spelling of a skill name (unknown names are returned stripped, original case)."""
    key = name.strip().lower()
    if key in SKILL_ALIASES:
        return SKILL_ALIASES[key]
    return _LOWER_CANON.get(key, name.strip())


def extract_skills(text: str) -> list[str]:
    found = set()
    for alias, canon in SKILL_ALIASES.items():
        if _ALIAS_RE[alias].search(text):
            found.add(canon)
    if "REST API" in found:  # "REST API" already says it, do not also report the generic "API"
        found.discard("API")
    return sorted(found)


def parse_skill_list(text: str) -> list[str]:
    """Skills from an explicit list line ("Languages: Python, Java, Kafka"): dictionary skills + short unknown items."""
    found = set(extract_skills(text))
    body = text.split(":", 1)[1] if re.match(r"^[^:,;]{2,30}:", text) else text  # drop a "Languages:" style label
    for item in re.split(r"[,;|•●▪/\n]+|\s{2,}", body):
        item = re.sub(r"\(.*?\)", "", item).strip(" .-–—*•\t")
        if not item or len(item) > 28 or len(item.split()) > 3 or not re.match(r"[A-Za-z0-9]", item):
            continue
        if _NOT_SKILLS.match(item) or _BAD_ITEM.search(item):
            continue
        if extract_skills(item):  # contains a known skill already (e.g. "Hands-on with Airflow"): not a new skill
            continue
        canon = canonical(item)
        if canon.lower() not in {s.lower() for s in found}:
            found.add(canon)
    return sorted(found)


def match_skill(skill: str, have: set[str] | list[str]) -> tuple[str, list[str]]:
    """How well does the set of skills `have` cover `skill`?  Returns (status, evidence skills)."""
    have_set = set(have)
    lower = {h.lower(): h for h in have_set}
    if skill.lower() in lower:
        return "matched", [lower[skill.lower()]]
    full = sorted(h for h in have_set if h in IMPLIED_BY.get(skill, ()))
    if full:
        return "matched", full
    part = sorted(h for h in have_set if h in RELATED_TO.get(skill, ()))
    if part:
        return "partial", part
    return "missing", []
