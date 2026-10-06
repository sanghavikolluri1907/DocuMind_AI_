# DocuMind AI

**Intelligent Resume & Job Description Analysis System**

DocuMind AI is an AIML academic project that analyzes resumes and job descriptions instead of acting as a generic PDF chatbot.

## Core workflow

Resume + Job Description → Document Parsing → Information/Skill Extraction → Resume Scoring → Semantic Matching → Skill Gap Analysis → Recommendations

## Features

- PDF, DOCX and TXT resume parsing
- Resume information extraction
- Skill extraction
- Resume quality scoring
- Job description analysis
- Resume/job semantic matching
- Matching, missing and partial skills
- Skill gap prioritization
- Resume improvement suggestions
- Career recommendations
- SQLite analysis history
- **Mock Interview: personalised practice interview with answer scoring and feedback (new)**
- Local-first processing
- Streamlit dashboard

## AIML concepts

- NLP and text preprocessing
- Rule-assisted information extraction
- Sentence embeddings
- Semantic similarity
- Cosine similarity
- Similarity-based scoring
- Recommendation logic
- Semantic answer evaluation (key-point coverage using embeddings + cosine similarity)

The matching engine combines explicit skill overlap with embeddings from `all-MiniLM-L6-v2`.

## How matching works (v2)

- **Resume parsing** finds sections by heading and keeps **each project as one entry** (title + all its bullet/wrapped lines), whatever layout is used: `Name - description`, `Name | tech | year` followed by bullets, numbered lists, or title lines with a paragraph below. DOCX tables are read too.
- **Job-description parsing** is section-aware: *Required*, *Preferred / nice to have*, *Responsibilities* and *Education* are separated. "X is a plus" demotes only X; degree names ("B.Tech in Machine Learning") never become skill requirements.
- **Skill matching** uses explicit rules: MySQL counts as SQL, TensorFlow as Machine Learning, GitHub as Git; related skills (AWS vs Azure, Pandas vs Data Analysis) give partial credit. Every result shows its evidence and whether the skill is proven in a project.
- **Score** = 70% skill coverage (required skills count most) + 15% semantic similarity + 15% relevance of your best two projects. Each project is scored individually in *Resume vs Job Match -> Project by project*.
- Semantic similarity uses sentence embeddings and falls back to TF-IDF automatically if the model cannot be downloaded.
- Run the self-checks with `python tests/test_matching.py` and `python tests/test_interview_engine.py`.

## Installation — Windows

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The first semantic comparison can download the Sentence Transformer model. Later runs reuse the cached model.

## How to use

1. Open **Resume Analyzer** and upload a PDF, DOCX or TXT resume.
2. Open **Job Description Analyzer** and upload/paste a job description.
3. Open **Resume vs Job Match** and run the matching analysis.
4. Review Skill Gap Analysis.
5. Review Resume Improvements and Career Recommendations.
6. Open **Mock Interview** to practise (see below).
7. Save the analysis from the sidebar and review it in Analysis History (resume analyses and mock interviews each have a tab).

## Mock Interview (voice, camera, different questions every time)

Take a basic mock interview inside the app, built from **your resume and/or job description**. You need at least one of them analysed first (and for the best questions, run **Resume vs Job Match** too).

### How it works

1. **Setup**: choose the number of questions (3-10), difficulty (Beginner / Intermediate), focus (Mixed, Technical, Projects, Behavioral & HR) and whether feedback appears after each answer or only at the end.
2. **Question generation** (`modules/interview_engine.py`) creates a personalised set:
   - **HR**: "Tell me about yourself", role fit, strengths and growth (uses your education, skills and matching skills)
   - **Technical**: questions for your skills that the job asks for first (from a curated bank, with a generic fallback for any other skill)
   - **Project**: questions about *your own* projects and the technologies you used in them
   - **Gap**: "The job asks for AWS but it is not on your resume. How would you get up to speed?" (from the Skill Gap results)
   - **Behavioral**: STAR-style questions (teamwork, problem solving, learning, mistakes, deadlines)
3. **The interviewer speaks.** Each question is read aloud using your browser's built-in text-to-speech (Web Speech API, free, nothing is uploaded). It plays automatically; use **🔊 Replay question** if you did not hear it (browsers sometimes need one click on the page first). You can change the speaking speed or switch voice off in the setup.
4. **Camera self-view.** When the interview starts the browser asks for **camera permission**. A live self-view appears beside the question so you can practise eye contact and posture. The video stays inside your browser tab: **it is not recorded, saved or uploaded**. You can turn it off at any time, and the interview works without it. (If the permission is blocked, click the camera/lock icon in the address bar, allow it and reload. It works on `http://localhost`.)
5. **Answer by voice.** Press **🎙 Start speaking** above the answer box and talk; your words appear live in the box (browser speech-to-text, Chrome or Edge, microphone permission required; Chrome's recogniser may send audio to the browser vendor's speech service). Press **⏹ Stop**, fix any mistakes, then **Submit**. You can still just type. Pick English (US/India/UK) next to the mic. You can skip a question or end early.
6. **Evaluation** (local, free, no paid API): every question has 3-4 *key points* a good answer should contain. A key point is counted as covered if a related keyword appears **or** its sentence embedding is semantically close (cosine similarity) to a sentence in your answer. Score (0-10) = 80% key-point coverage + 20% answer depth, with small penalties for very short answers and filler words. If the Sentence Transformer model is not available, scoring falls back to keyword matching only.
7. **Report**: overall practice score, score by category, strengths, weak areas, topics to revise, habit tips, a question-by-question review with the key ideas a strong answer covers, and a downloadable `.txt` report.
8. **History**: finished interviews can be saved to local SQLite (new `interviews` table), reviewed and deleted in **Analysis History -> Mock Interviews**.

> The interview score is a **practice estimate** of how well your answer covers key ideas. It does not predict real interview results, and the questions do not replace preparation with a real person.

### Why every interview is different

- A large question pool: 39 skills with 76 curated questions (several for the main skills), generic templates that work for *any* skill, 5-6 different question types per project, 12 behavioural questions, extra HR questions and several phrasings for the intro and skill-gap questions.
- **Question memory:** DocuMind stores only the *text* of questions that were asked (table `asked_questions`, never your answers) and prefers questions and skills you have not been asked yet. After 5 consecutive interviews on the sample data, 24+ of the 30 questions were different.
- Randomised ordering of skills (important skills still come early) and random choice among equally good questions.
- Reset the memory any time from **Analysis History -> Mock Interviews -> Reset question memory**.

### Browser notes

Use a recent **Chrome or Edge** (best text-to-speech voices and camera support). Firefox and Safari work for most parts, but voices differ. Voice and camera are optional; the interview works without them.

### Mock interview viva questions

**How does the interviewer "speak"?**  
The browser's Web Speech API (`speechSynthesis`) reads the question text. It runs locally on your device, so no audio or text leaves your computer.

**How is the camera used and is it private?**  
`getUserMedia` shows a live preview only. DocuMind does not record, store or analyse the video. It exists so you can practise body language.

**How do you make sure questions are not repeated?**  
Every asked question is counted in SQLite. When building a new interview, questions and skills with a lower "times asked" count are preferred, with random tie-breaking.


**How are questions personalised?**  
Skills are prioritised using the job description and match results (skills the job requires and you have come first), project questions use your own project text, and gap questions use the missing skills from the match.

**How are answers scored without an LLM?**  
Each question stores key points. An answer earns credit for a key point through keyword evidence or through sentence-embedding cosine similarity (>= 0.55 full credit, >= 0.42 half credit). Coverage and answer length are combined into a 0-10 score.

**Why use embeddings for answer scoring?**  
A candidate can explain a concept with different words ("memorises the training data" vs "overfits"). Embeddings measure meaning, so correct answers are not penalised for wording.

**What are the limitations?**  
It cannot verify factual correctness beyond key-point coverage, the question bank is limited to common skills (others use generic templates), answers are typed (speech-to-text is a future enhancement), and the camera is only a self-view (no body-language analysis).

## Project structure

```
documind_ai/
├── app.py
├── requirements.txt
├── modules/
│   ├── document_parser.py   resume_parser.py   jd_parser.py
│   ├── skill_extractor.py   similarity_engine.py
│   ├── resume_analyzer.py   scoring.py   skill_gap.py   recommendations.py
│   ├── interview_engine.py  (question generation + answer evaluation)
│   ├── interview_bank.py    (question data: curated + templates)
│   ├── interview_media.py   (voice + camera components)
│   └── interview_ui.py      (Mock Interview pages)
├── database/database.py     (analyses + interviews tables)
├── sample_data/
└── tests/test_interview_engine.py
```

Quick self-check of the interview engine (no internet needed): `python tests/test_interview_engine.py`

## Scoring

The resume score is an application-specific heuristic based on detected skills, projects, education, experience, certifications and contact information. It is not an official ATS score.

The job match combines:
- explicit skill overlap
- partial matching
- semantic similarity

It is a decision-support estimate, not a hiring prediction.

## Privacy

Resume files are processed in the running application. Analysis history and (optionally) mock-interview answers are stored locally in SQLite (`database/documind.db`) and can be deleted from Analysis History. Avoid sending sensitive documents to external services.

## Limitations

Document layouts vary, so extraction can be imperfect. Skill extraction is based on a curated vocabulary and can be expanded. Semantic similarity improves matching but cannot understand every recruiting nuance.

## Future enhancements

- More robust NER models
- Editable skill dictionary
- Recruiter mode
- Multi-resume comparison
- Job recommendation
- Resume export
- Local LLM-assisted rewriting
- Spoken answers with speech-to-text, timed answers, and body-language feedback from the camera
- Larger question bank and follow-up questions based on previous answers
- Multilingual document support

## Viva questions

**Why embeddings?**  
Embeddings represent text as vectors, allowing semantically related phrases to be compared beyond exact keyword matches.

**What is cosine similarity?**  
It measures the angle between two vectors. Values closer to 1 indicate greater directional similarity.

**Why Sentence Transformers?**  
They provide compact sentence-level representations suitable for semantic comparison.

**Why SQLite?**  
It is lightweight, local and sufficient for a student project.

**Why is this not a PDF chatbot?**  
Documents are analyzed automatically to produce structured insights, matching, scores and recommendations. Question answering is not the primary workflow.

## Resume description

**DocuMind AI — Intelligent Resume & Job Description Analysis System**  
Built an NLP-based Streamlit application that parses resumes and job descriptions, extracts skills, computes semantic similarity using Sentence Transformers and cosine similarity, identifies skill gaps, scores resumes, and generates actionable improvement recommendations. Added a personalised mock-interview module (voice-based interviewer, camera self-view, non-repeating question sets) that generates HR, technical, project and behavioural questions from the resume and job description and scores answers using key-point coverage and sentence-embedding cosine similarity.
