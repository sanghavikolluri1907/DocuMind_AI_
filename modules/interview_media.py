"""Browser-side voice and camera for the mock interview.

* Voice  : the question is read aloud with the browser's built-in Web Speech API (speechSynthesis).
           Free, works offline with the system voices, no extra Python package, nothing is sent anywhere.
* Camera : a live self-view using navigator.mediaDevices.getUserMedia. The browser shows its own permission
           prompt. The video stays inside your browser tab: it is NOT recorded, saved or uploaded.
* Mic    : the answer can be SPOKEN. The browser's speech recognition (Web Speech API) turns your voice into text and
           types it live into the "Your answer" box, so you can edit it and press Submit as usual.
All three run in small HTML components, so they work on http://localhost (a secure context for browsers).
"""
from __future__ import annotations

import json

import streamlit as st

try:  # st.components.v1.html is the stable API for embedding small HTML/JS widgets
    from streamlit.components.v1 import html as _html
except Exception:  # pragma: no cover - very old/new Streamlit builds
    _html = None


def _safe_json(text: str) -> str:
    """JSON string that is safe to embed inside a <script> block."""
    return json.dumps(text).replace("</", "<\\/")


def _embed(markup: str, height: int):
    if _html is None:
        st.caption("Voice/camera components are not available in this Streamlit version.")
        return
    try:
        _html(markup, height=height)
    except Exception as exc:  # never let a UI widget crash the interview
        st.caption(f"Could not load the voice/camera component ({type(exc).__name__}).")


def speech_markup(text: str, rate: float = 0.95, auto_play: bool = True) -> str:
    return f"""
<div style="font-family:system-ui,Segoe UI,Arial,sans-serif;display:flex;align-items:center;gap:8px;flex-wrap:wrap">
  <button id="play" style="padding:6px 12px;border-radius:8px;border:1px solid #7c8aa5;background:#f5f7fb;cursor:pointer">🔊 Replay question</button>
  <button id="stop" style="padding:6px 12px;border-radius:8px;border:1px solid #7c8aa5;background:#f5f7fb;cursor:pointer">⏹ Stop</button>
  <span id="status" style="font-size:12px;color:#667085"></span>
</div>
<script>
(function () {{
  const TEXT = {_safe_json(text)};
  const RATE = {float(rate)};
  const AUTO = {str(bool(auto_play)).lower()};
  const status = document.getElementById("status");
  const synth = window.speechSynthesis;
  if (!synth) {{
    status.textContent = "Voice is not supported in this browser (try Chrome or Edge).";
    document.getElementById("play").disabled = true;
    return;
  }}
  function pickVoice() {{
    const voices = synth.getVoices().filter(v => (v.lang || "").toLowerCase().startsWith("en"));
    return voices.find(v => /natural|google|online/i.test(v.name)) || voices[0] || null;
  }}
  function speak() {{
    synth.cancel();
    const u = new SpeechSynthesisUtterance(TEXT);
    const v = pickVoice();
    if (v) {{ u.voice = v; u.lang = v.lang; }} else {{ u.lang = "en-US"; }}
    u.rate = RATE;
    u.onstart = () => status.textContent = "Interviewer is speaking…";
    u.onend = () => status.textContent = "";
    u.onerror = () => status.textContent = "Press 🔊 to hear the question (the browser may need a click first).";
    synth.speak(u);
  }}
  document.getElementById("play").onclick = speak;
  document.getElementById("stop").onclick = () => {{ synth.cancel(); status.textContent = ""; }};
  window.addEventListener("pagehide", () => synth.cancel());
  if (AUTO) {{
    if (synth.getVoices().length) {{ speak(); }}
    else {{ synth.onvoiceschanged = () => {{ synth.onvoiceschanged = null; speak(); }}; setTimeout(() => {{ if (!synth.speaking) speak(); }}, 600); }}
  }}
}})();
</script>
"""


def speech_input_markup(question_id: str) -> str:
    """Dictation widget. Types the recognised speech into the Streamlit 'Your answer' textarea of the parent page.

    The component iframe is same-origin with the Streamlit page, so it can reach the textarea directly.
    `question_id` is embedded so the widget starts fresh for every question.
    """
    return f"""
<div style="font-family:system-ui,Segoe UI,Arial,sans-serif;display:flex;align-items:center;gap:8px;flex-wrap:wrap">
  <button id="mic" style="padding:7px 14px;border-radius:8px;border:1px solid #7c8aa5;background:#f5f7fb;cursor:pointer;font-weight:600">🎙 Start speaking</button>
  <select id="lang" style="padding:6px;border-radius:8px;border:1px solid #7c8aa5;background:#fff">
    <option value="en-US">English (US)</option>
    <option value="en-IN">English (India)</option>
    <option value="en-GB">English (UK)</option>
  </select>
  <button id="clear" style="padding:6px 10px;border-radius:8px;border:1px solid #7c8aa5;background:#f5f7fb;cursor:pointer">Clear answer</button>
  <span id="status" style="font-size:12px;color:#667085"></span>
</div>
<!-- question: {question_id} -->
<script>
(function () {{
  const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
  const mic = document.getElementById("mic");
  const status = document.getElementById("status");
  const langSel = document.getElementById("lang");
  if (!Rec) {{
    status.textContent = "Speech-to-text is not supported in this browser. Use Chrome or Edge, or type your answer.";
    mic.disabled = true;
    return;
  }}
  const P = window.parent;
  const getBox = () => P.document.querySelector('textarea[aria-label="Your answer"]');
  function setBox(value) {{
    const ta = getBox();
    if (!ta) return false;
    const setter = Object.getOwnPropertyDescriptor(P.HTMLTextAreaElement.prototype, "value").set;
    setter.call(ta, value);
    ta.dispatchEvent(new P.Event("input", {{ bubbles: true }}));
    return true;
  }}
  function commit() {{ // blur makes Streamlit save the text so Submit sees it
    const ta = getBox();
    if (ta) {{ ta.focus(); ta.blur(); }}
  }}
  let rec = null, listening = false, base = "", finalText = "";
  function join(a, b) {{ a = (a || "").trim(); b = (b || "").trim(); return a && b ? a + " " + b : a || b; }}

  function start() {{
    const ta = getBox();
    if (!ta) {{ status.textContent = "Could not find the answer box on this page."; return; }}
    try {{ P.speechSynthesis && P.speechSynthesis.cancel(); }} catch (e) {{}}
    base = ta.value || "";
    finalText = "";
    rec = new Rec();
    rec.lang = langSel.value;
    rec.continuous = true;
    rec.interimResults = true;
    rec.onstart = () => {{ listening = true; mic.textContent = "⏹ Stop"; status.textContent = "Listening… speak your answer."; }};
    rec.onresult = (ev) => {{
      let interim = "";
      for (let i = ev.resultIndex; i < ev.results.length; i++) {{
        const t = ev.results[i][0].transcript;
        if (ev.results[i].isFinal) finalText = join(finalText, t); else interim += t;
      }}
      setBox(join(base, join(finalText, interim)));
    }};
    rec.onerror = (e) => {{
      const m = {{
        "not-allowed": "Microphone permission was blocked. Click the lock icon in the address bar, allow the microphone, then reload.",
        "service-not-allowed": "Speech recognition is blocked in this browser.",
        "no-speech": "I did not hear anything. Check your microphone and try again.",
        "audio-capture": "No microphone was found.",
        "network": "Speech recognition needs an internet connection in this browser."
      }};
      status.textContent = m[e.error] || ("Speech error: " + e.error);
      if (e.error === "not-allowed" || e.error === "service-not-allowed" || e.error === "audio-capture") listening = false;
    }};
    rec.onend = () => {{ // Chrome ends the session after a pause: restart while the user has not pressed Stop
      if (listening) {{ base = getBox() ? getBox().value : base; finalText = ""; try {{ rec.start(); }} catch (e) {{}} return; }}
      mic.textContent = "🎙 Start speaking"; commit();
      if (!status.textContent.startsWith("Mic") && !/blocked|found|connection|supported/.test(status.textContent)) status.textContent = "Stopped. Edit the text if needed, then press Submit.";
    }};
    try {{ rec.start(); }} catch (e) {{ status.textContent = "Could not start the microphone: " + e.message; }}
  }}
  function stop() {{ listening = false; if (rec) {{ try {{ rec.stop(); }} catch (e) {{}} }} }}
  mic.onclick = () => (listening ? stop() : start());
  document.getElementById("clear").onclick = () => {{ stop(); setBox(""); commit(); status.textContent = "Answer cleared."; }};
  window.addEventListener("pagehide", stop);
}})();
</script>
"""


CAMERA_MARKUP = """
<div style="font-family:system-ui,Segoe UI,Arial,sans-serif">
  <div id="box" style="position:relative">
    <video id="cam" autoplay muted playsinline
      style="width:100%;border-radius:12px;background:#0f172a;transform:scaleX(-1);display:block;min-height:120px"></video>
  </div>
  <div id="msg" style="font-size:12px;color:#667085;margin:6px 0">Requesting camera access…</div>
  <button id="toggle" style="display:none;padding:5px 10px;border-radius:8px;border:1px solid #7c8aa5;background:#f5f7fb;cursor:pointer">Turn camera off</button>
</div>
<script>
(function () {
  const video = document.getElementById("cam");
  const msg = document.getElementById("msg");
  const toggle = document.getElementById("toggle");
  let stream = null;
  async function start() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      msg.textContent = "Camera is not available here (a browser with camera support and http://localhost or https is required).";
      return;
    }
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480, facingMode: "user" }, audio: false });
      video.srcObject = stream;
      video.style.display = "block";
      msg.textContent = "Camera on: self-view only. Nothing is recorded or uploaded.";
      toggle.textContent = "Turn camera off";
      toggle.style.display = "inline-block";
    } catch (e) {
      const denied = e && (e.name === "NotAllowedError" || e.name === "SecurityError");
      const missing = e && (e.name === "NotFoundError" || e.name === "OverconstrainedError");
      msg.textContent = denied
        ? "Camera permission was blocked. Click the camera/lock icon in the address bar, allow the camera, then reload the page. The interview still works without it."
        : missing ? "No camera was found on this device. The interview still works without it."
                  : "Camera could not start: " + (e && e.message ? e.message : "unknown error");
    }
  }
  function stop() {
    if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
    video.srcObject = null;
  }
  toggle.onclick = () => {
    if (stream) { stop(); video.style.display = "none"; msg.textContent = "Camera turned off."; toggle.textContent = "Turn camera on"; }
    else { start(); }
  };
  window.addEventListener("pagehide", stop);
  start();
})();
</script>
"""


def render_voice(question_text: str, rate: float = 0.95, auto_play: bool = True):
    """Read `question_text` aloud (auto-plays once when the question appears; replay button always available)."""
    _embed(speech_markup(question_text, rate, auto_play), height=48)


def render_camera():
    """Live self-view panel. The HTML is identical on every rerun so the camera keeps running between questions."""
    _embed(CAMERA_MARKUP, height=300)
    st.caption("Tips: look at the lens, sit upright, keep light in front of you, and speak your answer out loud before typing it.")


def render_voice_input(question_id: str):
    """Mic button that dictates the answer into the 'Your answer' box (Chrome/Edge)."""
    _embed(speech_input_markup(question_id), height=56)
