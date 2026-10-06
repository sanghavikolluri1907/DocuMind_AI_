"""Question data for the mock interview (kept separate from the logic in interview_engine.py).

Every question has KEY POINTS: ideas a good answer should contain, with keywords that indicate each idea.
More questions per skill + several phrasings = a different interview every time.
"""
from __future__ import annotations


def kp(point: str, *keywords: str) -> dict:
    """Key point: an idea a good answer should contain, plus keywords that indicate it."""
    return {"point": point, "keywords": [k.lower() for k in keywords]}


def Q(level: str, question: str, *points: dict) -> dict:
    return {"level": level, "question": question, "points": list(points)}


# ---------------------------------------------------------------- extra curated technical questions
EXTRA_TECH_BANK: dict[str, list[dict]] = {
    "Python": [
        Q("Beginner", "What do *args and **kwargs do in Python functions?",
          kp("*args collects extra positional arguments into a tuple", "args", "positional", "tuple"),
          kp("**kwargs collects extra keyword arguments into a dictionary", "kwargs", "keyword", "dictionary", "dict"),
          kp("They make functions flexible about how many arguments they accept", "flexible", "any number", "variable number", "unknown number")),
        Q("Beginner", "How does exception handling work in Python?",
          kp("Code that may fail goes in a try block and errors are caught with except", "try", "except", "catch"),
          kp("finally (or else) runs cleanup code or code for the success case", "finally", "else", "cleanup", "clean up"),
          kp("Catch specific exceptions instead of a bare except, and raise your own errors when needed", "specific", "raise", "bare", "custom")),
        Q("Intermediate", "What are decorators in Python and when would you use one?",
          kp("A decorator is a function that wraps another function to add behaviour", "wrap", "function that", "adds behaviour", "adds behavior", "modif"),
          kp("Typical uses: logging, timing, authentication or caching", "logging", "timing", "authentication", "cache", "caching", "login"),
          kp("It is applied with the @decorator syntax", "@", "syntax", "above the function")),
        Q("Beginner", "What is the difference between a shallow copy and a deep copy?",
          kp("A shallow copy copies the outer object but shares inner objects", "shallow", "shares", "same inner", "reference"),
          kp("A deep copy recursively copies everything so objects are independent", "deep", "recursive", "independent", "everything"),
          kp("Matters with nested mutable objects such as lists inside lists; use the copy module", "nested", "copy module", "deepcopy", "mutable")),
    ],
    "SQL": [
        Q("Beginner", "What is the difference between DELETE, TRUNCATE and DROP?",
          kp("DELETE removes selected rows (with WHERE) and can be rolled back", "where", "rows", "rollback", "roll back", "delete"),
          kp("TRUNCATE removes all rows quickly but keeps the table structure", "all rows", "truncate", "structure", "quick"),
          kp("DROP removes the whole table including its structure", "drop", "entire table", "whole table", "removes the table")),
        Q("Intermediate", "What is an index in SQL and what are its trade-offs?",
          kp("An index speeds up searches, like the index of a book", "speed", "faster", "lookup", "search", "book"),
          kp("It costs extra storage and slows down inserts and updates", "storage", "slow", "insert", "update", "write"),
          kp("Create indexes on columns used often in WHERE or JOIN conditions", "where", "join", "frequently", "often")),
        Q("Beginner", "What is normalization and why is it used?",
          kp("Organising data into related tables to reduce redundancy", "redundan", "duplicate", "related tables", "organi"),
          kp("Normal forms (1NF, 2NF, 3NF) guide how tables are split", "1nf", "2nf", "3nf", "normal form"),
          kp("It improves integrity, though heavy joins may justify denormalisation for speed", "integrity", "consisten", "denormali", "join")),
    ],
    "Machine Learning": [
        Q("Beginner", "What is the bias-variance trade-off?",
          kp("High bias means a model that is too simple and underfits", "bias", "underfit", "too simple"),
          kp("High variance means the model is too sensitive to training data and overfits", "variance", "overfit", "sensitive"),
          kp("The goal is a balanced model complexity that generalises well", "balance", "trade-off", "tradeoff", "generali", "complexity")),
        Q("Beginner", "When would you use classification and when regression? Give examples of each.",
          kp("Classification predicts categories, such as spam or not spam", "categor", "class", "label", "spam"),
          kp("Regression predicts continuous numbers, such as house price", "continuous", "number", "price", "numeric", "value"),
          kp("Algorithms: logistic regression, decision trees, SVM / linear regression, random forest", "logistic", "decision tree", "svm", "linear regression", "random forest")),
        Q("Intermediate", "Explain cross-validation and why we use it.",
          kp("Data is split into k folds; train on k-1 folds and validate on the remaining one", "fold", "k-fold", "split", "k-1"),
          kp("The process rotates so every fold is used for validation once, and scores are averaged", "rotate", "average", "each fold", "every fold", "mean"),
          kp("It gives a more reliable estimate and helps detect overfitting", "reliable", "robust", "overfit", "estimate", "single split")),
        Q("Beginner", "What is feature scaling and when is it needed?",
          kp("Scaling brings features to similar ranges (standardisation or min-max)", "standardi", "normali", "min-max", "range", "scale", "scaling"),
          kp("It matters for distance-based or gradient-based models like KNN, SVM and neural networks", "knn", "svm", "distance", "gradient", "neural"),
          kp("Fit the scaler on training data only to avoid data leakage", "leakage", "training data only", "fit on train", "fit the scaler")),
    ],
    "Deep Learning": [
        Q("Beginner", "What is gradient descent and what does the learning rate control?",
          kp("Gradient descent repeatedly updates weights to minimise the loss", "minimi", "loss", "update", "weights", "gradient"),
          kp("The learning rate sets the step size of each update", "step", "learning rate", "size"),
          kp("Too high a rate can diverge; too low makes training very slow", "diverge", "overshoot", "slow", "too high", "too low")),
        Q("Intermediate", "What are vanishing gradients and how can they be reduced?",
          kp("In deep networks gradients become tiny so early layers learn very slowly", "tiny", "small", "early layers", "vanish", "slowly"),
          kp("ReLU activations, careful weight initialisation and batch normalisation help", "relu", "initiali", "batch norm", "normalisation", "normalization"),
          kp("Residual connections, or LSTM/GRU for sequence models, also help", "residual", "skip connection", "lstm", "gru", "resnet")),
    ],
    "NLP": [
        Q("Beginner", "What is TF-IDF and why is it better than plain word counts?",
          kp("TF-IDF multiplies term frequency by inverse document frequency", "term frequency", "inverse document", "tf", "idf"),
          kp("It down-weights very common words that appear in most documents", "common words", "down-weight", "downweight", "stop word", "frequent"),
          kp("It highlights words that are distinctive for a document", "distinct", "important", "unique", "highlight", "specific")),
        Q("Intermediate", "What are word embeddings and how do they differ from TF-IDF?",
          kp("Embeddings are dense vectors that capture meaning", "dense", "vector", "meaning", "semantic"),
          kp("Similar words or sentences end up close together, measured with cosine similarity", "close", "cosine", "similar", "distance"),
          kp("TF-IDF is sparse and cannot capture synonyms or context", "sparse", "synonym", "context", "word2vec", "bert")),
    ],
    "Pandas": [
        Q("Beginner", "How do you combine two DataFrames, and what is the difference between merge and concat?",
          kp("merge joins DataFrames on key columns, like a SQL join", "merge", "join", "key", "on="),
          kp("concat stacks DataFrames along rows or columns", "concat", "stack", "append", "axis"),
          kp("The join type (inner, left, right, outer) controls which rows are kept", "inner", "left", "outer", "right", "how")),
        Q("Beginner", "How would you find and handle duplicate rows and outliers in a dataset?",
          kp("Use duplicated() and drop_duplicates() for duplicates", "duplicated", "drop_duplicates", "duplicate"),
          kp("Detect outliers with IQR, z-score or box plots", "iqr", "z-score", "zscore", "box plot", "boxplot", "outlier"),
          kp("Decide whether to remove, cap or investigate them instead of deleting blindly", "cap", "investigate", "domain", "decide", "remove", "winsor")),
    ],
    "NumPy": [
        Q("Beginner", "What does reshape do in NumPy and what is the axis argument?",
          kp("reshape changes the shape of an array without changing its data", "shape", "reshape", "without changing"),
          kp("axis=0 works down the rows (per column) while axis=1 works across columns (per row)", "axis=0", "axis=1", "axis", "rows", "columns"),
          kp("Example: np.sum(arr, axis=0) gives column totals", "sum", "mean", "example", "total")),
    ],
    "scikit-learn": [
        Q("Beginner", "What is a Pipeline in scikit-learn and why is it useful?",
          kp("A Pipeline chains preprocessing steps and a model into one object", "chain", "steps", "preprocess", "pipeline", "sequence"),
          kp("It prevents data leakage, especially during cross-validation", "leakage", "cross-validation", "cross validation", "leak"),
          kp("It makes code cleaner and the whole model easy to reuse or deploy, e.g. with GridSearchCV", "reuse", "deploy", "gridsearch", "clean", "tuning")),
    ],
    "Git": [
        Q("Beginner", "What is the difference between git merge and git rebase?",
          kp("merge combines branches and keeps history with a merge commit", "merge commit", "combine", "history", "merge"),
          kp("rebase replays your commits on top of another branch for a linear history", "replay", "linear", "on top", "rebase"),
          kp("Avoid rebasing branches that others already use", "shared", "public", "others", "avoid", "force push")),
        Q("Beginner", "How do you undo a mistake in Git, for example a wrong commit?",
          kp("git revert makes a new commit that undoes a change safely", "revert", "new commit", "safe"),
          kp("git reset moves the branch back (soft keeps changes, hard discards them)", "reset", "soft", "hard", "head"),
          kp("git stash or checkout/restore can recover or discard file changes", "stash", "checkout", "restore", "amend")),
    ],
    "Streamlit": [
        Q("Beginner", "How do widgets and layouts work in Streamlit? Name some you have used.",
          kp("Widgets such as button, slider, selectbox or file_uploader return the user's input", "button", "slider", "selectbox", "file_uploader", "text_input", "widget"),
          kp("Layout tools: columns, tabs, sidebar and expanders", "columns", "tabs", "sidebar", "expander", "container", "layout"),
          kp("Keys and callbacks help manage state between reruns", "key", "callback", "state", "session")),
        Q("Intermediate", "How would you deploy a Streamlit app and keep secrets such as API keys safe?",
          kp("Deployment options: Streamlit Community Cloud, Docker or your own server", "community cloud", "docker", "server", "deploy", "cloud", "heroku"),
          kp("Keep secrets in st.secrets or environment variables, never in the code", "secrets", "environment variable", "env", "never commit", "toml"),
          kp("List dependencies in requirements.txt and exclude secrets with .gitignore", "requirements", "gitignore", "dependenc")),
    ],
    "Docker": [
        Q("Beginner", "How is a container different from a virtual machine?",
          kp("Containers share the host operating-system kernel, so they are lightweight and start quickly", "kernel", "share", "lightweight", "fast", "host"),
          kp("A virtual machine runs a full guest operating system and is heavier", "guest", "full operating", "heavier", "hypervisor", "virtual machine"),
          kp("Both give isolation; containers are more portable and efficient for apps", "isolat", "portable", "efficient", "resources")),
    ],
    "AWS": [
        Q("Intermediate", "What is the difference between EC2 and Lambda, and when would you choose each?",
          kp("EC2 gives virtual servers that you configure and manage", "server", "virtual", "manage", "configure", "ec2"),
          kp("Lambda is serverless: code runs on events and you pay per execution", "serverless", "event", "pay per", "lambda", "trigger"),
          kp("Choose EC2 for long-running workloads and Lambda for short event-driven tasks", "long-running", "long running", "short", "workload", "choose")),
    ],
    "REST API": [
        Q("Intermediate", "What is the difference between PUT and PATCH, and what does idempotent mean?",
          kp("PUT replaces a whole resource", "replace", "whole", "entire", "put"),
          kp("PATCH updates only part of a resource", "partial", "part", "patch", "only"),
          kp("An idempotent request gives the same result however many times it is repeated", "idempotent", "same result", "repeat", "multiple times"))],
    "Data Analysis": [
        Q("Beginner", "How would you communicate analysis findings to a non-technical audience?",
          kp("Lead with the key insight or answer, not the method", "insight", "key finding", "answer", "start with", "summary"),
          kp("Use simple visuals such as charts or a dashboard", "chart", "visual", "dashboard", "graph"),
          kp("Link the findings to impact and a clear recommendation, avoiding jargon", "impact", "recommend", "jargon", "action", "business"))],
    "JavaScript": [
        Q("Beginner", "What is the difference between == and === in JavaScript, and what is a promise?",
          kp("== compares after type coercion while === compares value and type strictly", "coerc", "strict", "type", "==="),
          kp("A promise represents the eventual result of an asynchronous operation", "eventual", "asynchronous", "async", "promise"),
          kp("Use then/catch or async/await to handle promises", "then", "catch", "await", "async"))],
    "LLM": [
        Q("Beginner", "What is prompt engineering and which techniques improve a model's answers?",
          kp("Give clear instructions and enough context", "clear", "instruction", "context", "specific"),
          kp("Use examples (few-shot), a role, or a required output format", "few-shot", "few shot", "example", "role", "format"),
          kp("Iterate and evaluate the outputs, e.g. step-by-step reasoning prompts", "iterate", "evaluate", "step by step", "step-by-step", "chain of thought", "test"))],
}

# ---------------------------------------------------------------- generic templates (work for ANY skill)
def generic_tech_questions(skill: str) -> list[dict]:
    s = skill.lower()
    return [
        Q("Beginner", f"Explain what {skill} is, where you have used it (or would use it), and one limitation or challenge to be aware of.",
          kp(f"A clear definition and purpose of {skill}", s, "used for", "purpose", "helps", "allows", "is a"),
          kp("A concrete example of where it is used (project or scenario)", "project", "example", "built", "for instance", "applied", "used it"),
          kp("A limitation, trade-off or challenge", "limitation", "challenge", "drawback", "trade-off", "however", "issue", "difficult")),
        Q("Beginner", f"Where would you use {skill} in a real project, and what alternative would you compare it with?",
          kp("A realistic use case", "use case", "project", "application", "for example", "scenario", "used to"),
          kp("An alternative or competing option", "alternative", "instead", "compare", "other option", "versus", " vs ", "similar to"),
          kp("The trade-offs that decide the choice", "trade-off", "because", "advantage", "disadvantage", "depends", "easier", "faster")),
        Q("Beginner", f"What is a common mistake or pitfall when using {skill}, and how do you avoid it?",
          kp("A specific, realistic pitfall", "mistake", "pitfall", "error", "problem", "issue", "common"),
          kp("How you avoid or fix it (best practice)", "avoid", "best practice", "prevent", "fix", "check", "test", "documentation"),
          kp("An example from your own practice", "i ", "my project", "once", "example", "when i")),
        Q("Beginner", f"How would you explain {skill} to a teammate who has never used it?",
          kp("A simple definition or analogy", "simple", "like a", "analogy", "basically", "is a", s),
          kp("The main benefit or reason it is used", "benefit", "helps", "useful", "because", "saves", "allows"),
          kp("A small example or first step to get started", "example", "start", "first", "install", "tutorial", "try")),
    ]


# ---------------------------------------------------------------- behavioural + HR pools
BEHAVIORAL_POOL = [
    ("Tell me about a time you worked in a team on a project. What was your role?", "Teamwork"),
    ("Describe a technical problem you got stuck on. How did you solve it?", "Problem solving"),
    ("Tell me about a time you had to learn a new technology quickly.", "Learning agility"),
    ("Tell me about a mistake you made in a project and what you learned from it.", "Ownership"),
    ("Describe a disagreement in a team and how you handled it.", "Conflict handling"),
    ("How do you manage deadlines when exams and projects overlap?", "Time management"),
    ("Tell me about a time you received critical feedback. How did you respond?", "Handling feedback"),
    ("Describe a time you took initiative on something nobody asked you to do.", "Initiative"),
    ("Tell me about a project that did not go as planned. What did you do?", "Resilience"),
    ("How would you handle a teammate who is not contributing to a group project?", "Collaboration"),
    ("Tell me about a time you explained a technical idea to a non-technical person.", "Communication"),
    ("Describe a situation where you had to make a decision with incomplete information.", "Decision making"),
]

INTRO_PHRASINGS = [
    "Tell me about yourself.",
    "Walk me through your background and what brought you to this field.",
    "Give me a short introduction about yourself and your journey so far.",
]

GAP_PHRASINGS = [
    "The job asks for {skill}, which I can't see on your resume. How would you get up to speed on it, and what related experience could you build on?",
    "Imagine you join the team and your first task needs {skill}, which you haven't used professionally. How would you handle it?",
    "I notice {skill} is important for this role but is not listed in your profile. What is your plan to close that gap?",
]


def hr_extra_questions(resume_skills: list[str]) -> list[dict]:
    skills = [s.lower() for s in resume_skills[:10]]
    return [
        {"skill": "Career goals", "level": "Beginner", "question": "Where do you see yourself in three years?",
         "points": [kp("A clear direction or target role", "role", "engineer", "developer", "analyst", "scientist", "position", "career"),
                    kp("Skills you want to build", "skills", "learn", "master", "expertise", "improve", "technolog"),
                    kp("How this job fits that path", "this role", "this job", "this position", "opportunity", "company", "fits", "grow")]},
        {"skill": "Value you bring", "level": "Beginner", "question": "Why should we hire you over other candidates?",
         "points": [kp("Relevant skills or projects", "skills", "project", "experience", "built", *skills),
                    kp("Learning ability and attitude", "learn", "quick", "adapt", "curious", "dedicat", "eager", "attitude"),
                    kp("How you would add value to the team", "contribute", "add value", "help", "team", "bring", "impact"),
                    kp("Evidence or an example that backs the claims", "for example", "for instance", "example", "i built", "i developed", "i worked")]},
        {"skill": "Motivation", "level": "Beginner", "question": "What motivates you to work in AI and machine learning?",
         "points": [kp("A genuine source of interest, such as a project or problem", "interest", "fascinat", "excited", "curious", "problem", "project"),
                    kp("What you enjoy or find meaningful about the field", "enjoy", "impact", "solve", "data", "innovation", "meaningful"),
                    kp("How you pursue it (learning, practice, projects)", "learn", "course", "practice", "project", "kaggle", "read", "build")]},
        {"skill": "Continuous learning", "level": "Beginner", "question": "How do you keep your technical skills up to date?",
         "points": [kp("Specific learning resources", "course", "documentation", "blog", "youtube", "book", "tutorial", "coursera", "paper", "newsletter"),
                    kp("Hands-on practice with projects", "project", "practice", "build", "hands-on", "hands on", "kaggle", "code"),
                    kp("Consistency, community or a schedule", "daily", "weekly", "regular", "consisten", "community", "routine", "schedule", "group")]},
    ]
