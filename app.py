import hashlib

import pandas as pd
import streamlit as st
from modules.document_parser import extract_text
from modules.resume_parser import parse_resume
from modules.jd_parser import parse_job_description
from modules.similarity_engine import compare_resume_to_jd
from modules.resume_analyzer import analyze_resume
from modules.scoring import calculate_resume_score
from modules.recommendations import generate_recommendations
from modules.skill_gap import build_skill_gap
from database.database import init_db, save_analysis, get_history, delete_analysis
from modules.interview_ui import render_mock_interview_page, render_interview_history
from ui_styles import inject_css, render_hero

st.set_page_config(page_title="DocuMind AI", page_icon="📄", layout="wide")
init_db()

inject_css()

if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "interview" not in st.session_state:
    st.session_state.interview = None
if "last_interview_score" not in st.session_state:
    st.session_state.last_interview_score = None

render_hero()

with st.sidebar:
    st.header("Navigation")
    NAV_ICONS = {
        "Dashboard": "🏠", "Resume Analyzer": "📑", "Job Description Analyzer": "💼",
        "Resume vs Job Match": "🎯", "Skill Gap Analysis": "📊", "Resume Improvements": "✍️",
        "Career Recommendations": "🚀", "Mock Interview": "🎤", "Analysis History": "🕘",
    }
    page = st.radio("Go to", list(NAV_ICONS), format_func=lambda p: f"{NAV_ICONS[p]}  {p}",
                    label_visibility="collapsed")
    st.divider()
    st.caption("Local-first document analysis. Scores are AI-generated estimates, not official ATS scores.")

def _invalidate_match():
    """A new resume or job description makes any earlier match / gap result stale."""
    for key in ("match", "skill_gap"):
        st.session_state.pop(key, None)

def _changed(key, text):
    digest = hashlib.md5(text.encode("utf-8", errors="ignore")).hexdigest()
    if st.session_state.get(key) != digest:
        st.session_state[key] = digest
        return True
    return False

def _chips(items, empty="None"):
    return "  ".join(f"`{i}`" for i in items) if items else empty

STATUS_LABEL = {"matched": "✅ Matched", "partial": "🟡 Partial", "missing": "❌ Missing"}

def load_resume():
    return st.session_state.get("resume_data")

def load_jd():
    return st.session_state.get("jd_data")

if page == "Dashboard":
    st.header("Dashboard")
    if not load_resume():
        st.info("Start by uploading a resume in **Resume Analyzer**.")
        st.write("### What DocuMind AI does")
        cols = st.columns(5)
        for c, (title, body) in zip(cols, [
            ("📑 Parse", "Extract structured information from PDF, DOCX and TXT."),
            ("🧠 Analyze", "Evaluate resume content and identify strengths."),
            ("🎯 Match", "Compare your profile with a target job description."),
            ("📈 Improve", "Find skill gaps and actionable improvements."),
            ("🎤 Practise", "Take a mock interview generated from your resume and target job.")
        ]):
            with c:
                st.markdown(f"**{title}**")
                st.write(body)
    else:
        r = load_resume()
        score = st.session_state.get("resume_score", 0)
        st.metric("Resume Score", f"{score}/100")
        if load_jd() and st.session_state.get("match"):
            st.metric("Job Match", f"{st.session_state.match['match_percentage']}%")
        c1, c2, c3 = st.columns(3)
        c1.metric("Skills Detected", len(r["skills"]))
        c2.metric("Projects", len(r["projects"]))
        c3.metric("Certifications", len(r["certifications"]))
        if st.session_state.get("last_interview_score") is not None:
            st.metric("Latest Mock Interview Score", f"{st.session_state.last_interview_score}/100")
        else:
            st.caption("🎤 Tip: practise with the **Mock Interview** page, built from your resume and job description.")
        st.subheader("Detected Skills")
        st.write(", ".join(r["skills"]) if r["skills"] else "No skills detected yet.")
        if st.session_state.get("skill_gap"):
            gap = st.session_state.skill_gap
            st.subheader("Top Skill Gaps")
            st.write(", ".join(gap["high_priority"]) or "No high-priority gaps.")

elif page == "Resume Analyzer":
    st.header("📑 Resume Analyzer")
    upload = st.file_uploader("Upload your resume", type=["pdf", "docx", "txt"])
    if upload:
        try:
            text = extract_text(upload)
            if len(text.strip()) < 50:
                st.warning("The document contains too little readable text.")
            else:
                data = parse_resume(text)
                analysis = analyze_resume(text, data)
                score = calculate_resume_score(data, analysis)
                if _changed("resume_hash", text):
                    _invalidate_match()
                st.session_state.resume_data = data
                st.session_state.resume_analysis = analysis
                st.session_state.resume_score = score
                st.session_state.resume_name = upload.name
                st.success("Resume analyzed successfully.")
                st.metric("Resume Score", f"{score}/100")
                cols = st.columns(3)
                cols[0].metric("Skills", len(data["skills"]))
                cols[1].metric("Projects", len(data["project_details"]))
                cols[2].metric("Certifications", len(data["certifications"]))
                st.subheader("Contact")
                st.write(f"**{data['name']}** · {data['email'] or 'no email found'} · {data['phone'] or 'no phone found'}")
                st.subheader("Skills")
                st.write(_chips(data["skills"], "No skills detected."))
                st.subheader(f"Projects ({len(data['project_details'])})")
                if not data["project_details"]:
                    st.info("No projects section was detected. Use a heading such as PROJECTS.")
                for i, p in enumerate(data["project_details"], 1):
                    with st.container(border=True):
                        st.markdown(f"**{i}. {p['name']}**")
                        st.write(p["description"] or "_No description found._")
                        st.caption("Technologies detected: " + (", ".join(p["skills"]) or "none"))
                for title, key in (("Education", "education"), ("Experience", "experience"), ("Certifications", "certifications")):
                    if data[key]:
                        st.subheader(title)
                        for item in data[key]:
                            st.write("• " + item)
                with st.expander("Raw extracted data (JSON)"):
                    st.json(data)
                st.subheader("Analysis")
                for item in analysis["findings"]:
                    st.write(("⚠️ " if item["type"] == "warning" else "💡 ") + item["message"])
        except Exception as e:
            st.error(f"Could not analyze the document: {e}")

elif page == "Job Description Analyzer":
    st.header("💼 Job Description Analyzer")
    upload = st.file_uploader("Upload job description", type=["pdf", "docx", "txt"])
    pasted = st.text_area("Or paste the job description", height=220)
    if st.button("Analyze Job Description", type="primary"):
        try:
            text = pasted.strip()
            if upload:
                text = extract_text(upload)
                if pasted.strip():
                    st.caption("Both a file and pasted text were given: the uploaded file is used.")
            if len(text) < 30:
                st.warning("Please provide a longer job description.")
            else:
                data = parse_job_description(text)
                if _changed("jd_hash", text):
                    _invalidate_match()
                st.session_state.jd_data = data
                st.session_state.jd_name = upload.name if upload else "Pasted Job Description"
                st.success("Job description analyzed.")
                if data["job_title"]:
                    st.subheader(data["job_title"])
                st.markdown("**Required skills**")
                st.success(", ".join(data["required_skills"]) or "None detected")
                st.markdown("**Preferred / nice-to-have skills**")
                st.info(", ".join(data["preferred_skills"]) or "None detected")
                st.caption("Skills mentioned only inside the duties are treated as nice-to-have when the job has an explicit Required section.")
                c1, c2 = st.columns(2)
                c1.markdown("**Experience:** " + (", ".join(data["experience_requirements"]) or "not stated"))
                c2.markdown("**Education:** " + (", ".join(data["education_requirements"]) or "not stated"))
                if data["responsibilities"]:
                    st.markdown("**Responsibilities**")
                    for r in data["responsibilities"]:
                        st.write("• " + r)
                with st.expander("Raw extracted data (JSON)"):
                    st.json(data)
        except Exception as e:
            st.error(f"Could not analyze the job description: {e}")

elif page == "Resume vs Job Match":
    st.header("🎯 Resume vs Job Match")
    r, j = load_resume(), load_jd()
    if not r or not j:
        st.warning("Analyze both a resume and a job description first.")
    else:
        if st.button("Run Matching Analysis", type="primary"):
            with st.spinner("Calculating semantic similarity and skill overlap..."):
                match = compare_resume_to_jd(r, j)
                st.session_state.match = match
                st.session_state.skill_gap = build_skill_gap(r["skills"], j["required_skills"], match)
        match = st.session_state.get("match")
        if match:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Job Match", f"{match['match_percentage']}%")
            m2.metric("Required skills covered", "n/a" if match["required_coverage"] is None else f"{match['required_coverage']}%")
            m3.metric("Preferred skills covered", "n/a" if match["preferred_coverage"] is None else f"{match['preferred_coverage']}%")
            m4.metric("Text similarity", "n/a" if match["semantic_similarity"] is None else f"{match['semantic_similarity']:.0f}%")
            a, b, c = st.columns(3)
            a.metric("Matching", len(match["matching_skills"]))
            b.metric("Partial", len(match["partial_skills"]))
            c.metric("Missing", len(match["missing_skills"]))
            tab_skills, tab_projects = st.tabs(["Skill by skill", "Project by project"])
            with tab_skills:
                if match["skill_details"]:
                    st.dataframe(pd.DataFrame([{
                        "Skill": d["skill"], "Importance": d["importance"].title(),
                        "Status": STATUS_LABEL[d["status"]], "Evidence": d["note"]} for d in match["skill_details"]]),
                        hide_index=True)
                else:
                    st.info("No skills were recognised in the job description.")
            with tab_projects:
                if not match["project_matches"]:
                    st.info("No projects were found on the resume to compare.")
                for p in match["project_matches"]:
                    with st.container(border=True):
                        st.markdown(f"**{p['name']}**: {p['label']} relevance ({p['relevance']}/100)")
                        st.progress(p["relevance"] / 100)
                        if p["description"]:
                            st.caption(p["description"])
                        st.write("Job skills shown: " + (", ".join(p["matched_skills"]) or "none")
                                 + (f" · related: {', '.join(p['partial_skills'])}" if p["partial_skills"] else ""))
            st.caption(match["explanation"])

elif page == "Skill Gap Analysis":
    st.header("📊 Skill Gap Analysis")
    gap = st.session_state.get("skill_gap")
    if not gap:
        st.info("Run Resume vs Job Match first.")
    else:
        st.subheader("High Priority")
        st.write(", ".join(gap["high_priority"]) or "None")
        st.subheader("Medium Priority")
        st.write(", ".join(gap["medium_priority"]) or "None")
        if gap.get("low_priority"):
            st.subheader("Low Priority")
            st.write(", ".join(gap["low_priority"]))
        for g in gap.get("details", []):
            st.caption(f"{g['skill']}: {g['reason']}")
        st.subheader("Strengths")
        st.write(", ".join(gap["strengths"]) or "None")

elif page == "Resume Improvements":
    st.header("✍️ Resume Improvements")
    analysis = st.session_state.get("resume_analysis")
    if not analysis:
        st.info("Analyze a resume first.")
    else:
        for item in analysis["improvements"]:
            with st.container(border=True):
                st.markdown(f"**Original:** {item['original']}")
                st.markdown(f"**Suggested:** {item['suggestion']}")
                st.caption(item["reason"])

elif page == "Career Recommendations":
    st.header("🚀 Career Recommendations")
    r, j = load_resume(), load_jd()
    if not r:
        st.info("Analyze a resume first.")
    else:
        recs = generate_recommendations(r, j, st.session_state.get("match"))
        for section, values in recs.items():
            st.subheader(section)
            for value in values:
                st.write("• " + value)

elif page == "Mock Interview":
    render_mock_interview_page()

elif page == "Analysis History":
    st.header("🕘 Analysis History")
    tab_analyses, tab_interviews = st.tabs(["Resume Analyses", "Mock Interviews"])
    with tab_analyses:
        rows = get_history()
        if not rows:
            st.info("No saved analyses yet.")
        else:
            for row in rows:
                with st.container(border=True):
                    st.write(f"**{row['resume_name']}** — {row['created_at']}")
                    st.write(f"Resume score: {row['resume_score']} | Job match: {row['match_percentage']}%")
                    if st.button("Delete", key=f"del_{row['id']}"):
                        delete_analysis(row["id"])
                        st.rerun()
    with tab_interviews:
        render_interview_history()

with st.sidebar:
    if st.session_state.get("resume_data") and st.session_state.get("match"):
        if st.button("💾 Save Current Analysis"):
            m = st.session_state.match
            save_analysis(
                st.session_state.get("resume_name", "Resume"),
                st.session_state.get("jd_name", "Job Description"),
                st.session_state.get("resume_score", 0),
                m["match_percentage"],
                m["matching_skills"],
                m["missing_skills"]
            )
            st.success("Analysis saved.")
