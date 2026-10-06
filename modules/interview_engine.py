"""Mock-interview engine for DocuMind AI.

Pipeline
    resume + job description (+ match result)
        -> build_interview()   : picks personalised questions (HR, technical, project, gap, behavioural)
        -> evaluate_answer()   : scores each answer against "key points" a good answer should contain
        -> summarize_interview(): overall score, category scores, strengths, weak areas, tips

How an answer is scored (all local, no paid API):
    * Every question carries 3-4 KEY POINTS (ideas a good answer should mention).
    * A key point counts as covered if
        (a) one of its keywords appears in the answer, OR
        (b) its sentence-embedding is semantically close (cosine similarity) to a sentence of the answer
            -> this is why a correct answer using different words still gets credit.
      If the Sentence Transformer model is unavailable, only keyword matching is used.
    * Score (0-10) = 80% key-point coverage + 20% answer depth (length), minus small penalties for very
      short answers / heavy filler words.
This is a practice tool, NOT a prediction of real interview results.
"""
from __future__ import annotations

import math
import random
import re
from statistics import mean

from .interview_bank import (BEHAVIORAL_POOL, EXTRA_TECH_BANK, GAP_PHRASINGS, INTRO_PHRASINGS, Q, generic_tech_questions,
                             hr_extra_questions, kp)
from .skill_extractor import extract_skills

SEMANTIC_FULL = 0.55      # cosine similarity treated as "covered"
SEMANTIC_PARTIAL = 0.42   # cosine similarity treated as "partly covered"
FILLERS = ["um", "uh", "basically", "you know", "kind of", "sort of", "i guess", "actually", "like"]
EXPECTED_WORDS = {"Technical": 30, "Project": 55, "Behavioral": 60, "HR": 40, "Gap": 45}

CATEGORY_TIPS = {
    "Technical": "Define the concept in one sentence, explain how it works, then give a small example from your own practice.",
    "Project": "Cover: problem -> your role -> technologies -> challenge -> result. Be specific about what YOU did.",
    "Behavioral": "Use the STAR method: Situation, Task, Action (what you did), Result (what happened / what you learned).",
    "HR": "Keep it structured and honest: background, strengths with evidence, and what you want next.",
    "Gap": "Be honest about your current level, show a concrete learning plan, and link it to skills you already have.",
}


# ----------------------------------------------------------------------------- technical question bank
TECH_BANK: dict[str, list[dict]] = {
    "Python": [
        Q("Beginner", "What is the difference between a list and a tuple in Python, and when would you use each?",
          kp("Lists are mutable while tuples are immutable", "mutable", "immutable", "cannot be changed", "can be changed", "modify"),
          kp("Tuples suit fixed data and are hashable, so they can be dictionary keys", "fixed", "hashable", "dictionary key", "constant", "read-only"),
          kp("Lists suit collections that grow or change, for example appending items", "append", "dynamic", "grow", "add items", "change")),
        Q("Intermediate", "Explain list comprehensions and generators. When would a generator be the better choice?",
          kp("A list comprehension builds a whole list in memory in a compact syntax", "comprehension", "compact", "one line", "concise", "in memory"),
          kp("Generators yield values lazily, one at a time, using yield", "yield", "lazy", "lazily", "one at a time", "iterator"),
          kp("Generators save memory for large or streaming data", "memory", "large", "stream", "efficient")),
    ],
    "Java": [
        Q("Beginner", "What are the four pillars of object-oriented programming? Explain any two with an example.",
          kp("Encapsulation, abstraction, inheritance and polymorphism", "encapsulation", "abstraction", "inheritance", "polymorphism"),
          kp("An accurate explanation of at least one pillar (e.g. inheritance reuses a parent class)", "reuse", "parent", "child", "override", "hide", "data hiding"),
          kp("A concrete example such as Animal/Dog or Shape/Circle", "example", "class", "object", "animal", "shape"))],
    "C++": [
        Q("Beginner", "What is the difference between a pointer and a reference in C++?",
          kp("A pointer stores a memory address and can be null or reassigned", "address", "null", "reassign", "pointer"),
          kp("A reference is an alias for an existing variable and must be initialised", "alias", "initial", "reference"),
          kp("Mention of use cases such as dynamic memory or passing by reference", "dynamic", "pass by", "function", "memory"))],
    "SQL": [
        Q("Beginner", "What is the difference between INNER JOIN and LEFT JOIN? Give a small example.",
          kp("INNER JOIN returns only rows that match in both tables", "only", "matching", "both tables", "match"),
          kp("LEFT JOIN returns all rows from the left table, with NULLs where there is no match", "all rows", "left table", "null", "no match"),
          kp("A concrete example such as customers and orders", "example", "customers", "orders", "employees", "students")),
        Q("Intermediate", "Explain GROUP BY and the difference between WHERE and HAVING.",
          kp("GROUP BY groups rows so aggregate functions like COUNT or SUM can be applied per group", "group", "aggregate", "count", "sum", "avg"),
          kp("WHERE filters individual rows before grouping", "before group", "filters rows", "row", "where"),
          kp("HAVING filters groups after aggregation", "after group", "after aggregation", "having", "filters groups")),
    ],
    "MySQL": [
        Q("Beginner", "What are primary keys and foreign keys, and why do they matter in a relational database?",
          kp("A primary key uniquely identifies each row", "unique", "uniquely", "identif", "primary"),
          kp("A foreign key references a primary key in another table to link data", "reference", "link", "relationship", "another table", "foreign"),
          kp("They maintain integrity and avoid duplicate or inconsistent data", "integrity", "consistent", "duplicate", "constraint"))],
    "PostgreSQL": [
        Q("Beginner", "What are primary keys and foreign keys, and why do they matter in a relational database?",
          kp("A primary key uniquely identifies each row", "unique", "uniquely", "identif", "primary"),
          kp("A foreign key references a primary key in another table to link data", "reference", "link", "relationship", "another table", "foreign"),
          kp("They maintain integrity and avoid duplicate or inconsistent data", "integrity", "consistent", "duplicate", "constraint"))],
    "MongoDB": [
        Q("Beginner", "How does MongoDB differ from a relational database such as MySQL?",
          kp("MongoDB stores flexible JSON-like documents instead of fixed table rows", "document", "json", "bson", "flexible", "schema-less", "schemaless"),
          kp("Relational databases use fixed schemas, tables and joins", "table", "schema", "join", "relational"),
          kp("A use case where MongoDB's flexibility helps", "use case", "unstructured", "scale", "nested", "changing"))],
    "JavaScript": [
        Q("Beginner", "What is the difference between var, let and const in JavaScript?",
          kp("var is function-scoped and hoisted", "function-scoped", "function scope", "hoist"),
          kp("let and const are block-scoped", "block", "scope"),
          kp("const cannot be reassigned, while let can", "reassign", "constant", "cannot be changed"))],
    "React": [
        Q("Beginner", "What are components, props and state in React?",
          kp("Components are reusable UI building blocks", "reusable", "component", "building block", "ui"),
          kp("Props are inputs passed from parent to child and are read-only", "props", "parent", "read-only", "passed"),
          kp("State is data managed inside a component that triggers re-rendering when it changes", "state", "re-render", "rerender", "usestate", "changes"))],
    "Streamlit": [
        Q("Beginner", "How does a Streamlit app run, and how do you keep data between user interactions?",
          kp("Streamlit re-runs the script from top to bottom on every interaction", "rerun", "re-run", "top to bottom", "every interaction", "reruns"),
          kp("st.session_state stores values across reruns", "session_state", "session state", "persist", "keep values"),
          kp("Caching such as st.cache_data / st.cache_resource avoids repeating expensive work", "cache", "caching", "expensive", "model"))],
    "Flask": [
        Q("Beginner", "How do you create a simple REST endpoint in Flask, and what is a route?",
          kp("A route maps a URL path to a Python function", "route", "url", "maps", "decorator", "@app"),
          kp("HTTP methods such as GET and POST define the behaviour", "get", "post", "method", "http"),
          kp("Returning JSON (jsonify) for an API response", "json", "jsonify", "response", "return"))],
    "FastAPI": [
        Q("Beginner", "What advantages does FastAPI offer over Flask?",
          kp("Type hints with Pydantic give automatic request validation", "pydantic", "type hint", "validation", "validate"),
          kp("Automatic interactive API documentation (Swagger / OpenAPI)", "swagger", "openapi", "docs", "documentation"),
          kp("Async support and high performance", "async", "asynchronous", "fast", "performance"))],
    "Django": [
        Q("Beginner", "Explain Django's MVT architecture.",
          kp("Model handles data and the database layer (ORM)", "model", "orm", "database"),
          kp("View contains the request-handling logic", "view", "logic", "request"),
          kp("Template renders the HTML shown to the user", "template", "html", "render"))],
    "Pandas": [
        Q("Beginner", "What is a DataFrame, and how would you handle missing values in Pandas?",
          kp("A DataFrame is a two-dimensional labelled table of data", "table", "two-dimensional", "2d", "rows and columns", "labelled", "labeled"),
          kp("Detect missing values with isnull()/isna()", "isnull", "isna", "missing", "null", "nan"),
          kp("Handle them by dropping (dropna) or filling (fillna) with mean/median/mode", "dropna", "fillna", "drop", "fill", "mean", "median", "impute")),
        Q("Intermediate", "What is the difference between loc and iloc, and what does groupby do?",
          kp("loc selects by label while iloc selects by integer position", "label", "position", "index", "loc", "iloc"),
          kp("groupby splits data into groups so you can aggregate each group", "group", "split", "aggregate", "agg", "mean", "sum"))],
    "NumPy": [
        Q("Beginner", "Why is a NumPy array faster than a Python list for numerical work?",
          kp("NumPy arrays store elements of one type in contiguous memory", "contiguous", "same type", "homogeneous", "memory"),
          kp("Operations are vectorised and implemented in optimised C code", "vectori", "c code", "optimi", "no loop", "loops"),
          kp("Broadcasting and a rich set of mathematical functions", "broadcast", "function", "matrix", "linear algebra"))],
    "scikit-learn": [
        Q("Beginner", "Walk me through the steps of training and evaluating a model with scikit-learn.",
          kp("Split data into training and test sets (train_test_split)", "train_test_split", "split", "train", "test"),
          kp("Fit the model on training data and predict on test data", "fit", "predict", "model"),
          kp("Evaluate with metrics such as accuracy, precision, recall or F1 score", "accuracy", "precision", "recall", "f1", "metric", "score"),
          kp("Use pipelines or cross-validation to avoid leakage and get reliable results", "pipeline", "cross-validation", "cross validation", "leakage", "cv"))],
    "TensorFlow": [
        Q("Beginner", "What is a tensor, and how do you build and train a simple neural network in TensorFlow/Keras?",
          kp("A tensor is a multi-dimensional array of numbers", "multi-dimensional", "array", "n-dimensional", "tensor"),
          kp("Define layers (e.g. Sequential with Dense layers)", "sequential", "dense", "layer"),
          kp("Compile with a loss function and optimizer, then call fit", "compile", "loss", "optimizer", "fit", "epoch"))],
    "PyTorch": [
        Q("Beginner", "How does PyTorch differ from TensorFlow, and what is autograd?",
          kp("PyTorch builds dynamic computation graphs, which feels more Pythonic and eases debugging", "dynamic", "pythonic", "eager", "debug"),
          kp("Autograd automatically computes gradients for backpropagation", "autograd", "gradient", "backprop", "automatic"),
          kp("Training loop: forward pass, loss, backward, optimizer step", "forward", "loss", "backward", "optimizer", "step"))],
    "Machine Learning": [
        Q("Beginner", "What is the difference between supervised and unsupervised learning? Give an example of each.",
          kp("Supervised learning uses labelled data to learn a mapping from inputs to outputs", "label", "labeled", "labelled", "target", "supervised"),
          kp("Unsupervised learning finds patterns in unlabelled data", "unlabel", "unlabeled", "pattern", "structure", "without label"),
          kp("Examples: classification/regression vs clustering/dimensionality reduction", "classification", "regression", "clustering", "k-means", "pca", "example")),
        Q("Beginner", "What is overfitting and how can you reduce it?",
          kp("Overfitting means the model memorises training data and performs poorly on unseen data", "memoris", "memoriz", "unseen", "generali", "overfit"),
          kp("More data, simpler models or regularisation (L1/L2, dropout) help", "regulari", "more data", "simpler", "dropout", "l1", "l2"),
          kp("Use validation / cross-validation and early stopping to detect it", "validation", "cross-validation", "early stopping", "test set")),
        Q("Intermediate", "Which evaluation metrics would you use for a classification problem with imbalanced classes, and why not just accuracy?",
          kp("Accuracy can be misleading when one class dominates", "misleading", "dominate", "imbalanced", "majority"),
          kp("Precision, recall and F1-score give a fuller picture", "precision", "recall", "f1"),
          kp("Confusion matrix, ROC-AUC or resampling (SMOTE / class weights) can help", "confusion", "roc", "auc", "smote", "class weight", "resampl"))],
    "Deep Learning": [
        Q("Beginner", "What is a neural network, and what do activation functions do?",
          kp("A neural network is made of layers of connected neurons that learn weights from data", "layer", "neuron", "weights", "connected"),
          kp("Activation functions add non-linearity so the network can learn complex patterns", "non-linear", "nonlinear", "complex", "relu", "sigmoid", "softmax"),
          kp("Training uses backpropagation and gradient descent to update weights", "backprop", "gradient", "loss", "update")),
        Q("Intermediate", "What is a CNN and why is it suited to images?",
          kp("Convolution layers apply filters to detect local features such as edges", "filter", "kernel", "edge", "feature", "convolution"),
          kp("Weight sharing reduces parameters compared with fully connected layers", "parameters", "weight sharing", "shared", "fewer"),
          kp("Pooling layers downsample and give some translation invariance", "pooling", "downsampl", "invariance"))],
    "NLP": [
        Q("Beginner", "What preprocessing steps would you apply to text before building an NLP model?",
          kp("Cleaning and lowercasing the text, removing noise", "lowercase", "clean", "punctuation", "noise", "special character"),
          kp("Tokenisation and stop-word removal", "token", "stop word", "stopword"),
          kp("Stemming or lemmatisation to normalise word forms", "stemming", "lemmati", "normali"),
          kp("Converting text to numbers using TF-IDF, bag of words or embeddings", "tf-idf", "tfidf", "bag of words", "embedding", "vector"))],
    "Computer Vision": [
        Q("Beginner", "What is the difference between image classification and object detection?",
          kp("Classification assigns one label to the whole image", "whole image", "one label", "single label", "classif"),
          kp("Detection finds and localises multiple objects with bounding boxes", "bounding box", "locali", "multiple objects", "detect"),
          kp("Examples of models such as CNN/ResNet or YOLO", "cnn", "resnet", "yolo", "example"))],
    "OpenCV": [
        Q("Beginner", "What can you do with OpenCV? Describe a basic image-processing pipeline.",
          kp("Reading and resizing/converting images (e.g. grayscale)", "read", "imread", "resize", "grayscale", "convert"),
          kp("Filtering, thresholding or edge detection", "blur", "threshold", "edge", "canny", "filter"),
          kp("Using the result for detection or recognition tasks", "detect", "recogni", "contour", "face"))],
    "Generative AI": [
        Q("Beginner", "What is generative AI and how is it different from traditional discriminative models?",
          kp("Generative models create new content such as text, images or code", "generate", "create new", "text", "image", "content"),
          kp("Discriminative models classify or predict labels for given inputs", "classif", "predict", "label", "discriminative"),
          kp("Limitations such as hallucinations and bias", "hallucinat", "bias", "limitation", "incorrect"))],
    "LLM": [
        Q("Beginner", "What is a large language model and what are its main limitations?",
          kp("An LLM is a transformer-based model trained on large text data to predict the next token", "transformer", "next token", "predict", "trained", "large"),
          kp("Hallucinations and outdated knowledge", "hallucinat", "outdated", "incorrect", "made up"),
          kp("Mitigation with prompt design, retrieval (RAG) or fine-tuning", "prompt", "rag", "retrieval", "fine-tun", "fine tun"))],
    "RAG": [
        Q("Beginner", "Explain Retrieval-Augmented Generation (RAG) and why it is useful.",
          kp("Relevant documents are retrieved (using embeddings and vector search) for a query", "retriev", "embedding", "vector", "search"),
          kp("The retrieved context is added to the prompt of the LLM", "context", "prompt", "augment"),
          kp("It reduces hallucinations and lets the model use up-to-date or private data", "hallucinat", "up-to-date", "private", "grounded", "fresh"))],
    "Data Analysis": [
        Q("Beginner", "Describe the steps you follow when analysing a new dataset.",
          kp("Understand the problem and the data (columns, types, size)", "understand", "problem", "columns", "info", "shape"),
          kp("Clean the data: missing values, duplicates, outliers", "missing", "duplicate", "outlier", "clean"),
          kp("Explore with statistics and visualisations (EDA)", "eda", "visuali", "statistic", "plot", "explor"),
          kp("Draw conclusions or insights and communicate them", "insight", "conclusion", "report", "dashboard", "communicate"))],
    "Data Science": [
        Q("Beginner", "Describe the typical lifecycle of a data science project.",
          kp("Problem definition and data collection", "problem", "collect", "gather", "requirement"),
          kp("Cleaning, exploration and feature engineering", "clean", "explor", "feature", "eda"),
          kp("Model building and evaluation", "model", "train", "evaluat", "metric"),
          kp("Deployment and monitoring", "deploy", "monitor", "production"))],
    "Git": [
        Q("Beginner", "What is the difference between git pull and git fetch, and what is a merge conflict?",
          kp("git fetch downloads remote changes without merging them", "fetch", "without merging", "download"),
          kp("git pull is fetch plus merge into your current branch", "pull", "merge", "fetch and merge"),
          kp("A merge conflict happens when the same lines were changed in different branches and must be resolved manually", "conflict", "same line", "resolve", "manually")),
        Q("Intermediate", "How do branches help in teamwork, and what does a typical Git workflow look like?",
          kp("Branches let people work on features in isolation", "isolat", "feature", "branch", "parallel"),
          kp("Commit, push and open a pull request for review", "commit", "push", "pull request", "review"),
          kp("Merge into main after review and keep main stable", "merge", "main", "stable", "review"))],
    "GitHub": [
        Q("Beginner", "What is a pull request and why is it useful?",
          kp("A pull request proposes changes from one branch to another", "propose", "branch", "changes", "request"),
          kp("It enables code review and discussion before merging", "review", "discuss", "comment", "approve"),
          kp("It keeps the main branch stable and tracks history", "main", "stable", "history", "track"))],
    "Docker": [
        Q("Beginner", "What is Docker and what is the difference between an image and a container?",
          kp("Docker packages an application with its dependencies so it runs the same everywhere", "package", "dependenc", "consistent", "same everywhere", "portable"),
          kp("An image is a read-only template", "template", "blueprint", "read-only", "image"),
          kp("A container is a running instance of an image", "instance", "running", "container")),
        Q("Intermediate", "What is a Dockerfile and how would you containerise a Python application?",
          kp("A Dockerfile lists the instructions to build an image", "instruction", "build", "dockerfile"),
          kp("Typical steps: base image, copy code, install requirements, set the run command", "from", "copy", "pip install", "requirements", "cmd", "base image"),
          kp("Build the image and run the container with port mapping", "docker build", "docker run", "port", "expose"))],
    "AWS": [
        Q("Beginner", "Name some core AWS services and explain what they are used for.",
          kp("EC2 provides virtual servers", "ec2", "virtual server", "compute"),
          kp("S3 provides object storage", "s3", "storage", "bucket"),
          kp("IAM manages users and permissions, or other services like Lambda/RDS", "iam", "permission", "lambda", "rds", "access"))],
    "Azure": [Q("Beginner", "What are the main benefits of using a cloud platform such as Azure instead of on-premise servers?",
                kp("Pay-as-you-go pricing and lower upfront cost", "pay", "cost", "pricing"),
                kp("Scalability and elasticity on demand", "scal", "elastic", "on demand"),
                kp("Managed services, reliability and global availability", "managed", "reliab", "availability", "region"))],
    "GCP": [Q("Beginner", "What are the main benefits of using a cloud platform such as Google Cloud instead of on-premise servers?",
              kp("Pay-as-you-go pricing and lower upfront cost", "pay", "cost", "pricing"),
              kp("Scalability and elasticity on demand", "scal", "elastic", "on demand"),
              kp("Managed services, reliability and global availability", "managed", "reliab", "availability", "region"))],
    "REST API": [
        Q("Beginner", "What is a REST API? Explain common HTTP methods and status codes.",
          kp("A REST API exposes resources over HTTP using URLs", "resource", "url", "http", "endpoint"),
          kp("GET reads, POST creates, PUT/PATCH updates and DELETE removes", "get", "post", "put", "delete", "patch"),
          kp("Status codes such as 200, 201, 400, 404 and 500", "200", "404", "500", "status code", "201", "400")),
        ],
    "API": [
        Q("Beginner", "What is an API and how would you test one?",
          kp("An API lets two software systems communicate through defined requests and responses", "communicat", "interface", "request", "response"),
          kp("Common formats and methods such as JSON over HTTP", "json", "http", "get", "post"),
          kp("Testing with tools like Postman or automated unit tests", "postman", "test", "curl", "pytest"))],
    "Excel": [
        Q("Beginner", "Which Excel features would you use to analyse and summarise a large dataset?",
          kp("Pivot tables for summarising data", "pivot"),
          kp("Lookup and logical formulas such as VLOOKUP/XLOOKUP and IF", "vlookup", "xlookup", "if", "formula"),
          kp("Charts, filters or conditional formatting for presenting insights", "chart", "filter", "conditional", "visual"))],
    "Power BI": [
        Q("Beginner", "How would you build a dashboard in Power BI from raw data?",
          kp("Import and clean data (Power Query)", "import", "power query", "clean", "transform"),
          kp("Model relationships and create measures (DAX)", "relationship", "dax", "measure", "model"),
          kp("Build visuals and share the report", "visual", "chart", "publish", "share", "report"))],
    "Tableau": [
        Q("Beginner", "How would you build a dashboard in Tableau from raw data?",
          kp("Connect to a data source and prepare the data", "connect", "source", "prepare", "clean"),
          kp("Create worksheets with dimensions and measures", "dimension", "measure", "worksheet", "sheet"),
          kp("Combine them into an interactive dashboard with filters", "dashboard", "filter", "interactive"))],
}
for _skill, _questions in EXTRA_TECH_BANK.items():  # more questions per skill = more variety
    TECH_BANK.setdefault(_skill, []).extend(_questions)

GENERAL_AIML = [
    Q("Beginner", "What is the difference between supervised and unsupervised learning? Give an example of each.",
      *TECH_BANK["Machine Learning"][0]["points"]),
    Q("Beginner", "How do you approach debugging a program that produces wrong results?",
      kp("Reproduce the problem and read the error or output carefully", "reproduce", "error", "read", "output", "trace"),
      kp("Isolate the cause using prints, logging or a debugger", "print", "log", "debugger", "breakpoint", "isolate"),
      kp("Test the fix and add a test or note so it does not return", "test", "verify", "fix", "regression")),
]

STAR_POINTS = [
    kp("Set the situation or context", "when", "situation", "project", "during", "our team", "at that time", "semester", "college"),
    kp("State your task or responsibility", "my role", "my task", "responsible", "goal", "needed to", "had to", "objective", "i was"),
    kp("Explain the specific actions YOU took", " i built", " i decided", " i implemented", " i created", " i wrote", " i used", " i learned",
       " i started", " i tried", " i asked", " i organi", " i divided", " i researched", " i fixed", "implemented", "debugged", "solved"),
    kp("Share the result or what you learned", "result", "outcome", "as a result", "finally", "learned", "successfully", "improved",
       "achieved", "resolved", "completed", "accuracy", "reduced"),
]


# ----------------------------------------------------------------------------- variety helpers
def _empty_history() -> dict:
    return {"questions": {}, "skills": {}}


def _seen(history: dict, text: str) -> int:
    return history["questions"].get(text, 0)


def _least_seen(rng: random.Random, items: list[dict], history: dict, penalty=lambda q: 0):
    """Pick randomly among the candidates asked least often before (ties broken at random)."""
    if not items:
        return None
    rank = lambda q: (_seen(history, q["question"]), penalty(q))
    best = min(rank(q) for q in items)
    return rng.choice([q for q in items if rank(q) == best])


def _order_by_seen(rng: random.Random, items: list[dict], history: dict) -> list[dict]:
    """Shuffle, then put never/rarely asked questions first."""
    items = items[:]
    rng.shuffle(items)
    return sorted(items, key=lambda q: _seen(history, q["question"]))


# ----------------------------------------------------------------------------- question construction
def _project_title(text: str) -> str:
    title = re.split(r"\s[-–—:|]\s|:\s", text, maxsplit=1)[0].strip()
    return " ".join(title.split()[:7]) if len(title.split()) > 8 else title


def _tech_question(skill: str, level: str, rng: random.Random, history: dict, exclude: set[str]) -> dict | None:
    """One technical question for `skill`: curated ones first, generic templates when those are used up."""
    candidates = [{**q, "generic": False} for q in TECH_BANK.get(skill, [])]
    candidates += [{**q, "generic": True} for q in generic_tech_questions(skill)]
    candidates = [q for q in candidates if q["question"] not in exclude]

    def penalty(q: dict) -> int:  # keep difficulty close to the chosen level
        if level == "Intermediate":
            base = 0 if q["level"] == "Intermediate" else 1
        else:
            base = 0 if q["level"] == "Beginner" else 2
        return base + (1 if q["generic"] else 0)

    chosen = _least_seen(rng, candidates, history, penalty)
    if chosen is None:
        return None
    chosen = {k: v for k, v in chosen.items() if k != "generic"}
    return {**chosen, "category": "Technical", "skill": skill}


def _ordered_skills(skills: list[str], rng: random.Random, history: dict) -> list[str]:
    """Important skills stay likely to appear first, but order is randomised and recently asked skills are demoted."""
    keyed = [(i + rng.random() * 4 + 1.5 * history["skills"].get(s, 0), s) for i, s in enumerate(skills)]
    return [s for _, s in sorted(keyed)]


def _hr_questions(resume: dict | None, jd: dict | None, match: dict | None, rng: random.Random, history: dict):
    """Returns (intro_question, other_hr_questions)."""
    resume = resume or {}
    skills = [s.lower() for s in resume.get("skills", [])][:10]
    edu_words = [w for line in resume.get("education", [])[:2] for w in re.findall(r"[A-Za-z]{5,}", line.lower())][:8]
    intro_points = [
        kp("Your education or current background", "student", "studying", "pursuing", "b.tech", "btech", "engineering", "college",
           "university", "degree", *edu_words),
        kp("Your key skills and technologies", "skills", "proficient", "comfortable", "experience with", "knowledge of", *skills),
        kp("A project or practical work you are proud of", "project", "built", "developed", "created", "worked on"),
        kp("What you are looking for next", "looking for", "goal", "aspire", "want to", "interested in", "opportunity", "internship", "career"),
    ]
    phrase = min(INTRO_PHRASINGS, key=lambda t: (history["questions"].get(t, 0), rng.random()))
    intro = {"category": "HR", "skill": "Introduction", "level": "Beginner", "question": phrase, "points": intro_points}

    matching = [s.lower() for s in (match or {}).get("matching_skills", [])][:6]
    role_fit = {
        "category": "HR", "skill": "Role fit", "level": "Beginner",
        "question": "Why are you interested in this role, and what makes you a good fit for it?" if jd
        else "What kind of role are you looking for and why?",
        "points": [
            kp("Genuine motivation for the role or field", "interested", "excited", "passion", "motivat", "opportunity", "enjoy"),
            kp("Skills or experience that match the role", "skills", "experience", "my background", "match", "fit", *matching),
            kp("How you would contribute to the team", "contribute", "add value", "help the team", "bring", "support"),
            kp("Your wish to learn and grow", "grow", "learn", "develop my", "improve", "career"),
        ],
    }
    strengths = {
        "category": "HR", "skill": "Strengths & growth", "level": "Beginner",
        "question": "What are your strengths, and what is one area you are working to improve?",
        "points": [
            kp("A real strength backed by an example", "strength", "good at", "example", "for instance", "for example"),
            kp("An honest area for improvement", "weakness", "improve", "working on", "area", "struggle", "still learning"),
            kp("Concrete steps you take to improve", "practice", "course", "plan", "steps", "daily", "learning", "feedback"),
        ],
    }
    extras = [{**q, "category": "HR"} for q in hr_extra_questions(resume.get("skills", []))]
    others = [role_fit] + _order_by_seen(rng, [strengths] + extras, history)
    return intro, others


def _project_templates(title: str, techs: list[str]) -> list[dict]:
    """Several different questions that can be asked about the SAME project."""
    tech_kw = [t.lower() for t in techs] or ["python", "library", "framework", "tool", "language"]
    chosen = " and ".join(techs[:2])
    templates = [
        ("Project", f"Walk me through your project \"{title}\". What problem does it solve and what was your specific contribution?", [
            kp("The problem or goal the project addresses", "problem", "goal", "aim", "solve", "purpose", "objective", "built to", "designed to"),
            kp("Your specific role or contribution", " i ", "my role", "my contribution", "i built", "i developed", "i implemented", "i designed", "responsible"),
            kp(f"Technologies used ({', '.join(techs[:4]) or 'tools and libraries'})", *tech_kw),
            kp("Outcome, result or what you learned", "result", "outcome", "learned", "achieved", "working", "deployed", "tested", "accuracy", "users")]),
        ("Project", f"What was the biggest technical challenge in \"{title}\", and how did you debug or solve it?", [
            kp("A specific challenge or bug", "challenge", "problem", "issue", "error", "bug", "difficult", "stuck"),
            kp("The steps you took to investigate (logs, documentation, testing, experiments)", "logs", "print", "documentation", "google", "stack overflow", "tested", "tried", "debug", "investigat"),
            kp("How it was finally solved", "solved", "fixed", "solution", "resolved", "worked", "finally"),
            kp("What you learned from it", "learned", "lesson", "realised", "realized", "now i", "next time")]),
        ("Project", f"How did you test or evaluate that \"{title}\" works correctly? What did you measure?", [
            kp("Your testing approach (unit tests, sample data, manual testing)", "unit test", "pytest", "sample", "manual", "test case", "testing", "tested"),
            kp("Criteria or metrics used to judge success", "metric", "accuracy", "measure", "criteria", "performance", "speed", "precision", "success"),
            kp("Edge cases or errors you handled", "edge case", "error handling", "invalid", "empty", "exception", "corner case", "validation"),
            kp("Improvements made after testing", "improv", "fixed", "after testing", "changed", "refined", "optimi")]),
        ("Project", f"If you had two more weeks to work on \"{title}\", what would you improve or add, and why?", [
            kp("Specific improvements or features", "add", "feature", "improve", "enhance", "extend", "support", "integrat"),
            kp("The reasoning behind prioritising them", "because", "important", "priority", "users", "impact", "most useful"),
            kp("A technical approach for doing it", "using", "implement", "approach", "library", "model", "database", "api"),
            kp("Limitations of the current version", "limitation", "currently", "does not", "doesn't", "weakness", "not yet")]),
        ("Project", f"Describe the workflow of \"{title}\" from input to output. What happens at each step?", [
            kp("The input or data source", "input", "upload", "user", "data", "file", "dataset", "source"),
            kp("The main processing steps", "process", "step", "then", "parse", "clean", "extract", "train", "analy", "pipeline"),
            kp("The output or result shown to the user", "output", "result", "display", "dashboard", "report", "prediction", "shows"),
            kp("Where data is stored or how components connect", "database", "sqlite", "store", "save", "module", "function", "architecture")]),
    ]
    if techs:
        templates.append(("Project", f"In \"{title}\", why did you choose {chosen}? What alternatives did you consider and what challenges came up?", [
            kp(f"Reasons for choosing {chosen}", "because", "reason", "easy", "fast", "suited", "chose", "simple", "popular", "support", "lightweight", *[t.lower() for t in techs[:2]]),
            kp("Alternatives considered or trade-offs", "alternative", "instead", "compared", "other option", "trade-off", "versus", " vs ", "considered"),
            kp("A challenge you faced and how you handled it", "challenge", "problem", "issue", "error", "bug", "difficult", "solved", "fixed", "debug"),
            kp("What you would improve next", "improve", "next", "future", "would add", "enhance", "scale", "optimi")]))
    return [{"category": c, "question": q, "points": pts} for c, q, pts in templates]


def _project_questions(resume: dict | None, rng: random.Random, history: dict) -> list[dict]:
    """For every project, a random template; then (second pass) a different template about the same project."""
    entries = []
    for text in (resume or {}).get("projects", [])[:5]:
        if len(text.split()) < 4:
            continue
        title = _project_title(text)
        techs = [s["skill"] if isinstance(s, dict) else s for s in extract_skills(text)]
        entries.append((title, techs))
    rng.shuffle(entries)
    firsts, seconds, used = [], [], set()
    for title, techs in entries:
        pool = _project_templates(title, techs)
        for target in (firsts, seconds):
            pick = _least_seen(rng, [q for q in pool if q["question"] not in used], history)
            if pick:
                used.add(pick["question"])
                target.append({**pick, "skill": title, "level": "Beginner" if target is firsts else "Intermediate", "techs": techs})
    return firsts + seconds


def _gap_questions(resume: dict | None, jd: dict | None, match: dict | None, rng: random.Random, history: dict) -> list[dict]:
    if not jd:
        return []
    rskills = (resume or {}).get("skills", [])
    if match and match.get("missing_skills"):
        missing = list(match["missing_skills"])
    else:
        missing = [s for s in jd.get("required_skills", []) + jd.get("preferred_skills", []) if s not in rskills]
    missing = _ordered_skills(missing[:6], rng, history)  # most important first, but not always the same one
    questions = []
    for skill in missing[:3]:
        phrase = _least_seen(rng, [{"question": t.format(skill=skill)} for t in GAP_PHRASINGS], history)["question"]
        questions.append({
            "category": "Gap", "skill": skill, "level": "Intermediate", "question": phrase,
            "points": [
                kp("Honestly acknowledge your current level", "haven't", "have not", "not yet", "limited", "basic", "beginner", "new to",
                   "no experience", "little experience", "currently learning", "exposure", "don't have", "do not have"),
                kp("A concrete learning plan (courses, documentation, practice)", "plan", "course", "tutorial", "documentation", "practice",
                   "learn", "study", "workshop", "certification", "read"),
                kp("Related skills you already have that transfer", "similar", "related", "already", "experience with", "transfer",
                   "familiar", "my background", *[s.lower() for s in rskills[:8]]),
                kp("A realistic first step or timeline", "week", "month", "first", "start", "begin", "step", "daily", "timeline"),
            ],
        })
    return questions


def _behavioral_questions(rng: random.Random, history: dict) -> list[dict]:
    pool = [{"category": "Behavioral", "skill": topic, "level": "Beginner", "question": text, "points": STAR_POINTS}
            for text, topic in BEHAVIORAL_POOL]
    return _order_by_seen(rng, pool, history)


def _skill_priority(resume: dict | None, jd: dict | None, match: dict | None) -> list[str]:
    rskills = list((resume or {}).get("skills", []))
    ordered: list[str] = []
    if match:
        ordered += list(match.get("matching_skills", [])) + list(match.get("partial_skills", []))
    elif jd and rskills:
        ordered += [s for s in jd.get("required_skills", []) + jd.get("preferred_skills", []) if s in rskills]
    if not resume and jd:  # job description only
        ordered += list(jd.get("required_skills", [])) + list(jd.get("preferred_skills", []))
    ordered += rskills
    seen, result = set(), []
    for s in ordered:
        if s not in seen:
            seen.add(s)
            result.append(s)
    return result


def build_interview(resume: dict | None, jd: dict | None, match: dict | None = None, num_questions: int = 5,
                    level: str = "Beginner", focus: str = "Mixed", seed: int | None = None,
                    history: dict | None = None) -> list[dict]:
    """Create a personalised, DIFFERENT-EVERY-TIME list of interview questions.

    `history` = {"questions": {text: times_asked}, "skills": {skill: times_asked}} from earlier interviews.
    Questions/skills asked before are demoted so a new interview feels fresh; the random seed adds more variety.
    """
    if not resume and not jd:
        return []
    rng = random.Random(seed)
    history = history or _empty_history()
    history.setdefault("questions", {})
    history.setdefault("skills", {})
    n = max(1, int(num_questions))

    skills = _skill_priority(resume, jd, match)
    projects = _project_questions(resume, rng, history)
    if focus == "Projects":  # prefer technologies used inside the projects
        project_techs = [t for p in projects for t in p.get("techs", [])]
        skills = list(dict.fromkeys(project_techs + skills))
    skills = _ordered_skills(skills, rng, history)

    tech: list[dict] = []
    used_text: set[str] = set()
    for _ in range(3):  # pass 1: one question per skill; later passes add more questions for the same skills
        for skill in skills:
            q = _tech_question(skill, level, rng, history, used_text)
            if q:
                used_text.add(q["question"])
                tech.append(q)
        if len(tech) >= n * 2:
            break
    if not tech:
        tech = [{**q, "category": "Technical", "skill": "AI/ML basics"} for q in GENERAL_AIML]

    gap = _gap_questions(resume, jd, match, rng, history)
    behav = _behavioral_questions(rng, history)
    intro_q, extras = _hr_questions(resume, jd, match, rng, history)
    intro = [intro_q]

    def take(pool: list, k: int) -> list:
        k = max(0, min(k, len(pool)))
        taken, pool[:] = pool[:k], pool[k:]
        return taken

    chosen: list[dict] = []
    if focus == "Technical":
        chosen += take(gap, 1 if n >= 5 else 0)
        chosen += take(tech, n - len(chosen))
    elif focus == "Projects":
        chosen += take(projects, math.ceil(n * 0.6))
        chosen += take(tech, n - len(chosen))
    elif focus == "Behavioral & HR":
        chosen += take(intro, 1)
        chosen += take(extras, math.ceil(n * 0.4))
        chosen += take(behav, n - len(chosen))
    else:  # Mixed: every category represented
        n_gap = 1 if (n >= 6 and gap) else 0
        n_proj = min(len(projects), max(1, round(n * 0.15))) if projects else 0
        n_behav = max(1, round(n * 0.15)) if n >= 4 else 0
        n_tech = max(1, n - 1 - n_gap - n_proj - n_behav)
        chosen += take(intro, 1)
        chosen += take(tech, n_tech)
        chosen += take(projects, n_proj)
        chosen += take(gap, n_gap)
        chosen += take(behav, n_behav)
    for pool in (tech, projects, behav, gap, extras, intro):  # fill any remaining slots
        if len(chosen) >= n:
            break
        chosen += take(pool, n - len(chosen))
    chosen = chosen[:n]

    rank = {"HR": 3, "Technical": 1, "Project": 1, "Gap": 2, "Behavioral": 3}
    chosen = sorted(enumerate(chosen), key=lambda t: (0 if t[1].get("skill") == "Introduction" else rank[t[1]["category"]], t[0]))
    return [{**q, "id": f"q{i}", "tip": CATEGORY_TIPS[q["category"]]} for i, (_, q) in enumerate(chosen, start=1)]


# ----------------------------------------------------------------------------- answer evaluation
def warm_up_model() -> bool:
    """Load the Sentence Transformer (downloads once on first use). Returns False if unavailable."""
    try:
        from .similarity_engine import _get_model
        _get_model()
        return True
    except Exception:
        return False


def _semantic_best_similarity(points: list[dict], answer: str) -> list[float] | None:
    try:
        from .similarity_engine import _get_model
        model = _get_model()
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", answer) if len(s.split()) >= 3]
        windows = sentences + [" ".join(sentences[i:i + 2]) for i in range(len(sentences) - 1)]
        if not windows:
            windows = [answer]
        embeddings = model.encode([p["point"] for p in points] + windows, normalize_embeddings=True, show_progress_bar=False)
        point_vecs, window_vecs = embeddings[:len(points)], embeddings[len(points):]
        return (point_vecs @ window_vecs.T).max(axis=1).tolist()  # cosine similarity (vectors are normalised)
    except Exception:
        return None


def evaluate_answer(question: dict, answer: str, use_semantic: bool = True) -> dict:
    """Score one answer (0-10) and explain why. Works with keyword matching alone if embeddings fail."""
    answer = (answer or "").strip()
    padded = f" {answer.lower()} "
    words = re.findall(r"[A-Za-z0-9+#']+", answer)
    wc = len(words)
    points = question["points"]
    sims = _semantic_best_similarity(points, answer) if use_semantic and wc >= 3 else None

    covered, partial, missed = [], [], []
    credit = 0.0
    for i, p in enumerate(points):
        keyword_hit = any(k in padded for k in p["keywords"])
        sim = sims[i] if sims else 0.0
        if keyword_hit or sim >= SEMANTIC_FULL:
            covered.append(p["point"])
            credit += 1.0
        elif sim >= SEMANTIC_PARTIAL:
            partial.append(p["point"])
            credit += 0.5
        else:
            missed.append(p["point"])
    coverage = credit / max(1, len(points))

    expected = EXPECTED_WORDS.get(question["category"], 40)
    depth = min(1.0, wc / expected)
    score = 10 * (0.8 * coverage + 0.2 * depth)
    filler_count = sum(len(re.findall(rf"\b{re.escape(f)}\b", answer.lower())) for f in FILLERS if f != "like")
    if wc < 8:
        score = min(score, 2.0)
    elif wc < 15:
        score = min(score, 4.5)
    if filler_count >= 5:
        score -= 0.5
    score = round(max(0.0, min(10.0, score)), 1)

    strengths, improvements, flags = [], [], []
    if covered:
        strengths.append(f"You covered {len(covered)} of {len(points)} key ideas.")
    if wc >= expected:
        strengths.append("Good level of detail.")
    if question["category"] in ("Project", "Behavioral", "Gap", "HR") and re.search(r"\b(i|my)\b", answer.lower()):
        strengths.append("You spoke in first person and showed ownership.")
    if wc < expected:
        improvements.append(f"Your answer is short ({wc} words). Aim for roughly {expected}+ words with an example.")
        flags.append("short")
    if question["category"] in ("Project", "Behavioral") and not re.search(r"\d", answer):
        improvements.append("If true, add a concrete detail or measurable result (dataset size, accuracy, time saved, team size).")
        flags.append("no_metric")
    if question["category"] in ("Project", "Behavioral") and not re.search(r"\b(i|my)\b", answer.lower()):
        improvements.append("Say what YOU did (\"I built...\", \"I decided...\") instead of only describing the team or the system.")
        flags.append("no_ownership")
    if filler_count >= 3:
        improvements.append("Reduce filler words (um, basically, you know) to sound more confident.")
        flags.append("fillers")
    for point in (missed + partial)[:3]:
        improvements.append(f"Consider mentioning: {point}.")

    verdict = "Strong" if score >= 8 else "Good" if score >= 6 else "Fair" if score >= 4 else "Needs work"
    return {
        "id": question["id"], "category": question["category"], "skill": question.get("skill", ""),
        "question": question["question"], "answer": answer, "skipped": False, "score": score, "verdict": verdict,
        "word_count": wc, "covered": covered, "partial": partial, "missed": missed,
        "strengths": strengths, "improvements": improvements, "flags": flags,
        "reference_points": [p["point"] for p in points],
        "semantic_used": sims is not None,
    }


def skipped_result(question: dict) -> dict:
    return {"id": question["id"], "category": question["category"], "skill": question.get("skill", ""),
            "question": question["question"], "answer": "", "skipped": True, "score": 0.0, "verdict": "Skipped", "word_count": 0,
            "covered": [], "partial": [], "missed": [p["point"] for p in question["points"]], "strengths": [],
            "improvements": ["You skipped this question. Review the key ideas below and try again."], "flags": ["skipped"],
            "reference_points": [p["point"] for p in question["points"]], "semantic_used": False}


# ----------------------------------------------------------------------------- final report
def summarize_interview(results: list[dict]) -> dict:
    answered = [r for r in results if not r["skipped"]]
    if not answered:
        return {"overall": 0.0, "answered": 0, "total": len(results), "by_category": {}, "strengths": [], "weak_areas": [],
                "top_tips": [], "readiness": "No answers were submitted.", "study_topics": []}
    overall = round(mean(r["score"] for r in answered) * 10, 1)
    by_cat: dict[str, list[float]] = {}
    for r in answered:
        by_cat.setdefault(r["category"], []).append(r["score"] * 10)
    by_category = {c: round(mean(v), 1) for c, v in by_cat.items()}

    strengths = [f"{r['skill']} ({r['category']}): {r['score']}/10" for r in sorted(answered, key=lambda x: -x["score"]) if r["score"] >= 7][:4]
    weak = [r for r in sorted(answered, key=lambda x: x["score"]) if r["score"] < 6]
    weak_areas = [f"{r['skill']} ({r['category']}): {r['score']}/10" for r in weak][:4]
    study = []
    for r in weak:
        if r["category"] in ("Technical", "Gap") and r["skill"] not in study:
            study.append(r["skill"])

    flag_counts: dict[str, int] = {}
    for r in answered:
        for f in r["flags"]:
            flag_counts[f] = flag_counts.get(f, 0) + 1
    tip_text = {
        "short": "Give longer, more complete answers with an example.",
        "no_metric": "Add measurable details (numbers, results) wherever they are true.",
        "no_ownership": "Describe your own actions using \"I\" statements.",
        "fillers": "Cut filler words to sound more confident.",
    }
    top_tips = [tip_text[f] for f, _ in sorted(flag_counts.items(), key=lambda t: -t[1]) if f in tip_text][:3]

    if overall >= 75:
        readiness = "Strong practice performance. Keep refining examples and practise under time pressure."
    elif overall >= 55:
        readiness = "Good foundation. Work on the weaker areas below and add more specific examples."
    elif overall >= 35:
        readiness = "Developing. Revise the key ideas for the weaker questions and practise again."
    else:
        readiness = "Early stage. Revise the fundamentals, then retry the interview."
    return {"overall": overall, "answered": len(answered), "total": len(results), "by_category": by_category,
            "strengths": strengths, "weak_areas": weak_areas, "top_tips": top_tips, "readiness": readiness,
            "study_topics": study[:5]}


def report_to_text(summary: dict, results: list[dict], meta: dict) -> str:
    """Plain-text report for download."""
    lines = ["DocuMind AI - Mock Interview Report", "=" * 40,
             f"Resume: {meta.get('resume_name', '-')}", f"Job description: {meta.get('jd_name', '-')}",
             f"Level: {meta.get('level', '-')} | Focus: {meta.get('focus', '-')}",
             f"Overall practice score: {summary['overall']}/100 ({summary['answered']}/{summary['total']} answered)",
             summary["readiness"], "", "Note: practice estimate only, not a prediction of real interview outcomes.", ""]
    for i, r in enumerate(results, start=1):
        lines += [f"Q{i} [{r['category']}] {r['question']}", f"Score: {r['score']}/10 ({r['verdict']})",
                  f"Your answer: {r['answer'] or '(skipped)'}"]
        lines += [f"  + {s}" for s in r["strengths"]] + [f"  - {s}" for s in r["improvements"]]
        lines += ["  Key ideas a strong answer covers:"] + [f"    * {p}" for p in r["reference_points"]] + [""]
    return "\n".join(lines)
