"""Streamlit pages for the Mock Interview feature (setup -> live interview -> report) and its history view."""
import random
import uuid

import pandas as pd
import streamlit as st

from database.database import (clear_asked_questions, delete_all_interviews, delete_interview, get_asked_history,
                               get_interviews, record_asked_questions, save_interview)
from modules.interview_engine import (build_interview, evaluate_answer, report_to_text, skipped_result,
                                      summarize_interview, warm_up_model)
from modules.interview_media import render_camera, render_voice, render_voice_input

LEVELS = ["Beginner", "Intermediate"]
FOCUS_OPTIONS = ["Mixed", "Technical", "Projects", "Behavioral & HR"]
FEEDBACK_MODES = ["After each answer", "Only at the end"]
CATEGORY_ICON = {"Technical": "🧠", "Project": "🛠️", "Behavioral": "🤝", "HR": "👤", "Gap": "🎯"}
PRACTICE_NOTE = ("Practice tool only: scores estimate how well your answer covers the key ideas. "
                 "They are not a prediction of real interview results.")


# ------------------------------------------------------------------ helpers
def _show_feedback(res: dict):
    """Detailed feedback card for one answered question."""
    c1, c2 = st.columns([1, 3])
    c1.metric("Score", f"{res['score']}/10")
    c2.markdown(f"**{res['verdict']}** · {res['word_count']} words")
    if res["covered"]:
        st.markdown("**✅ Key ideas you covered**")
        for item in res["covered"]:
            st.write(f"- {item}")
    if res["partial"]:
        st.markdown("**🟡 Partly covered**")
        for item in res["partial"]:
            st.write(f"- {item}")
    if res["missed"]:
        st.markdown("**❌ Key ideas you could add**")
        for item in res["missed"]:
            st.write(f"- {item}")
    for item in res["strengths"]:
        st.success(item)
    for item in res["improvements"]:
        if not item.startswith("Consider mentioning"):  # missed ideas are already listed above
            st.warning(item)
    if not res.get("semantic_used") and not res["skipped"]:
        st.caption("Scored with keyword matching (the AI language model was not available).")


def _finish(iv: dict):
    summary = summarize_interview(iv["results"])
    summary["total"] = len(iv["questions"])
    iv["summary"] = summary
    iv["stage"] = "done"
    st.session_state.last_interview_score = summary["overall"]
    if iv["config"]["save_history"] and iv.get("saved_id") is None and summary["answered"] > 0:
        try:
            iv["saved_id"] = save_interview(
                iv["meta"]["resume_name"], iv["meta"]["jd_name"], iv["config"]["level"], iv["config"]["focus"],
                len(iv["questions"]), summary["answered"], summary["overall"], summary, iv["results"])
        except Exception as exc:  # database problems must never crash the app
            st.session_state.interview_save_error = f"Could not save to history: {exc}"


def _advance(iv: dict):
    iv["index"] += 1
    iv["pending_feedback"] = False
    if iv["index"] >= len(iv["questions"]):
        _finish(iv)


def _new_session(questions: list, config: dict, meta: dict) -> dict:
    return {"stage": "running", "sid": uuid.uuid4().hex[:8], "questions": questions, "index": 0, "results": [],
            "pending_feedback": False, "config": config, "meta": meta, "saved_id": None, "summary": None}


# ------------------------------------------------------------------ pages
def _render_setup():
    resume = st.session_state.get("resume_data")
    jd = st.session_state.get("jd_data")
    match = st.session_state.get("match")
    if not resume and not jd:
        st.warning("Analyze a resume (Resume Analyzer) and/or a job description (Job Description Analyzer) first. "
                   "The interview questions are generated from them.")
        return

    st.write("Practice a realistic interview **inside DocuMind AI**. Questions are generated from your own resume "
             "and the job you are targeting; your answers are scored locally.")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"**Resume:** {'✅ ' + str(st.session_state.get('resume_name', 'loaded')) if resume else '❌ not loaded'}")
    c2.markdown(f"**Job description:** {'✅ ' + str(st.session_state.get('jd_name', 'loaded')) if jd else '❌ not loaded'}")
    c3.markdown(f"**Match results:** {'✅ used to target gaps' if match else '➖ not run (optional)'}")

    with st.container(border=True):
        a, b, c = st.columns(3)
        num = a.slider("Number of questions", 3, 10, 5)
        level = b.selectbox("Difficulty", LEVELS, help="Beginner = fundamentals. Intermediate = deeper follow-ups.")
        focus = c.selectbox("Focus", FOCUS_OPTIONS)
        mode = st.radio("Feedback", FEEDBACK_MODES, horizontal=True,
                        help="'Only at the end' feels more like a real interview.")
        v1, v2, v3, v4 = st.columns(4)
        voice = v1.checkbox("🔊 Interviewer reads questions aloud", value=True,
                            help="Uses your browser's built-in text-to-speech. Nothing is sent anywhere.")
        rate = v2.slider("Speaking speed", 0.7, 1.3, 0.95, 0.05, disabled=not voice)
        camera = v3.checkbox("📷 Show my camera (self-view)", value=True,
                             help="Your browser will ask for camera permission. Video stays in your browser: it is not recorded, saved or uploaded.")
        mic = v4.checkbox("🎙 Answer by voice (speech-to-text)", value=True,
                          help="Speak your answer; it is typed into the answer box for you to review. Works in Chrome/Edge.")
        save_history = st.checkbox("Save this interview (questions, answers, scores) to local history", value=True,
                                   help="Stored only in the local SQLite file. You can delete it from Analysis History.")
    st.caption("🔀 Every interview uses different questions: DocuMind remembers which questions you were asked "
               "(question text only) and avoids repeating them. Reset this in Analysis History -> Mock Interviews.")

    if st.button("▶ Start mock interview", type="primary"):
        with st.spinner("Preparing questions and loading the AI language model "
                        "(first-time use downloads it once and can take a minute)..."):
            semantic = warm_up_model()
            try:
                history = get_asked_history()
            except Exception:  # memory is a bonus; never block the interview
                history = None
            questions = build_interview(resume, jd, match, num, level, focus, seed=random.randrange(10 ** 6), history=history)
        if not questions:
            st.error("Could not generate questions from the available data. Try a different focus.")
            return
        try:
            record_asked_questions(questions)
        except Exception:
            pass
        config = {"level": level, "focus": focus, "feedback_mode": mode, "semantic": semantic, "requested": num,
                  "save_history": save_history, "voice": voice, "rate": rate, "camera": camera, "mic": mic}
        meta = {"resume_name": st.session_state.get("resume_name", "-") if resume else "-",
                "jd_name": st.session_state.get("jd_name", "-") if jd else "-"}
        st.session_state.interview = _new_session(questions, config, meta)
        st.session_state.pop("interview_save_error", None)
        st.rerun()


def _render_question(iv: dict):
    questions = iv["questions"]
    total = len(questions)
    q = questions[iv["index"]]
    cfg = iv["config"]
    left, right = st.columns([3, 1.3]) if cfg.get("camera") else (st.container(), None)

    if right is not None:
        with right:  # first element of the column on every rerun, so the live camera is not restarted
            render_camera()

    with left:
        st.progress(iv["index"] / total, text=f"Question {iv['index'] + 1} of {total}")
        if total < cfg["requested"] and iv["index"] == 0:
            st.info(f"Only {total} questions could be generated from your data (you asked for {cfg['requested']}).")
        if not cfg["semantic"]:
            st.caption("AI language model unavailable: answers are scored by keyword matching only.")

        st.markdown(f"{CATEGORY_ICON.get(q['category'], '❓')} **{q['category']}** · {q['skill']} · {q['level']}")
        with st.container(border=True):
            st.markdown(f"### {q['question']}")
        if cfg.get("voice"):
            greeting = "Welcome to your mock interview. Let's begin. " if iv["index"] == 0 else ""
            render_voice(f"{greeting}Question {iv['index'] + 1} of {total}. {q['question']}", cfg.get("rate", 0.95))
        with st.expander("💡 How to approach this question"):
            st.write(q["tip"])

        if iv["pending_feedback"]:
            _show_feedback(iv["results"][-1])
            last = iv["index"] >= total - 1
            if st.button("Finish & see report ➜" if last else "Next question ➜", type="primary"):
                _advance(iv)
                st.rerun()
            return

        if cfg.get("mic", True):
            render_voice_input(f"{iv['sid']}_{q['id']}")
        answer = st.text_area("Your answer", key=f"answer_{iv['sid']}_{q['id']}", height=200,
                              placeholder="Press 🎙 Start speaking and answer out loud, or type here. You can edit the text before submitting.")
        b1, b2, b3 = st.columns([1, 1, 1])
        if b1.button("Submit answer", type="primary"):
            if len(answer.split()) < 3:
                st.warning("Please write at least a short answer (3+ words), or use Skip.")
            else:
                with st.spinner("Evaluating your answer..."):
                    res = evaluate_answer(q, answer, use_semantic=cfg["semantic"])
                iv["results"].append(res)
                if cfg["feedback_mode"] == FEEDBACK_MODES[0]:
                    iv["pending_feedback"] = True
                else:
                    _advance(iv)
                st.rerun()
        if b2.button("Skip question"):
            iv["results"].append(skipped_result(q))
            _advance(iv)
            st.rerun()
        if b3.button("End interview now"):
            _finish(iv)
            st.rerun()
        st.caption(PRACTICE_NOTE)


def _render_report(iv: dict):
    summary = iv["summary"]
    results = iv["results"]
    st.subheader("📋 Interview Report")
    if st.session_state.get("interview_save_error"):
        st.warning(st.session_state.interview_save_error)
    elif iv.get("saved_id"):
        st.success("Saved to your local Mock Interview history.")

    if summary["answered"] == 0:
        st.warning("No answers were submitted, so there is nothing to score. Start a new interview when you are ready.")
    else:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Overall practice score", f"{summary['overall']}/100")
        m2.metric("Answered", f"{summary['answered']}/{summary['total']}")
        m3.metric("Level", iv["config"]["level"])
        m4.metric("Focus", iv["config"]["focus"])
        st.info(summary["readiness"])
        st.caption(PRACTICE_NOTE)

        if summary["by_category"]:
            st.markdown("#### Score by category")
            df = pd.DataFrame({"Average score (0-100)": summary["by_category"]})
            st.bar_chart(df)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 💪 Strengths")
            for item in summary["strengths"] or ["Keep practising: no answer reached 7/10 yet."]:
                st.write(f"- {item}")
            st.markdown("#### 🧭 Habits to improve")
            for item in summary["top_tips"] or ["No recurring habits flagged. Nice work."]:
                st.write(f"- {item}")
        with col2:
            st.markdown("#### 🎯 Weak areas")
            for item in summary["weak_areas"] or ["No answers scored below 6/10."]:
                st.write(f"- {item}")
            if summary["study_topics"]:
                st.markdown("#### 📚 Topics to revise")
                st.write(", ".join(summary["study_topics"]))

    st.markdown("#### Question-by-question review")
    for i, res in enumerate(results, start=1):
        label = f"Q{i} · {res['category']} · {res['skill']} · {res['score']}/10 ({res['verdict']})"
        with st.expander(label):
            st.markdown(f"**Question:** {res['question']}")
            st.markdown(f"**Your answer:** {res['answer'] or '_skipped_'}")
            _show_feedback(res)
            with st.expander("Key ideas a strong answer covers"):
                for point in res["reference_points"]:
                    st.write(f"- {point}")

    report = report_to_text(summary, results, {**iv["meta"], **iv["config"]})
    st.download_button("⬇ Download report (.txt)", report, file_name="documind_mock_interview_report.txt")
    c1, c2 = st.columns(2)
    if c1.button("🔁 Retry the same questions"):
        st.session_state.interview = _new_session(iv["questions"], iv["config"], iv["meta"])
        st.session_state.pop("interview_save_error", None)
        st.rerun()
    if c2.button("🆕 New interview (different questions)"):
        st.session_state.interview = None
        st.session_state.pop("interview_save_error", None)
        st.rerun()


def render_mock_interview_page():
    st.header("🎤 Mock Interview")
    iv = st.session_state.get("interview")
    if iv is None:
        _render_setup()
    elif iv["stage"] == "running":
        _render_question(iv)
    else:
        _render_report(iv)


# ------------------------------------------------------------------ history
def render_interview_history():
    if st.button("🔀 Reset question memory (questions may repeat again)"):
        clear_asked_questions()
        st.success("Question memory cleared.")
    try:
        rows = get_interviews()
    except Exception as exc:
        st.error(f"Could not read interview history: {exc}")
        return
    if not rows:
        st.info("No saved mock interviews yet. Complete one in **Mock Interview** and keep 'Save' ticked.")
        return
    table = pd.DataFrame([{
        "ID": r["id"], "Date": r["created_at"], "Resume": r["resume_name"], "Job description": r["jd_name"],
        "Level": r["level"], "Focus": r["focus"], "Answered": f"{r['answered']}/{r['num_questions']}",
        "Score": r["overall_score"]} for r in rows])
    st.dataframe(table, hide_index=True)

    for r in rows:
        details = r["details"]
        with st.expander(f"Interview #{r['id']} · {r['created_at']} · score {r['overall_score']}/100"):
            summary = details.get("summary", {})
            if summary.get("readiness"):
                st.info(summary["readiness"])
            for res in details.get("results", []):
                st.markdown(f"**{res.get('category', '')} · {res.get('skill', '')}** — {res.get('score', 0)}/10")
                st.write(f"Q: {res.get('question', '')}")
                st.write(f"A: {res.get('answer') or '(skipped)'}")
                st.divider()
            if st.button("Delete this interview", key=f"del_iv_{r['id']}"):
                delete_interview(r["id"])
                st.rerun()

    st.divider()
    confirm = st.checkbox("I understand this deletes ALL saved mock interviews", key="confirm_del_all_iv")
    if st.button("🗑 Delete all interview history", disabled=not confirm):
        delete_all_interviews()
        st.rerun()
