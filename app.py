import streamlit as st
import time
import sys
import os
import textwrap

# ── Dependency probe — done once at module load, never crashes the app ────────
def _probe_deps() -> tuple[bool, str]:
    missing = []
    for pkg, imp in [("tavily-python", "tavily"), ("langchain-mistralai", "langchain_mistralai"),
                     ("langchain", "langchain"), ("beautifulsoup4", "bs4")]:
        try:
            __import__(imp)
        except ImportError:
            missing.append(pkg)
    if missing:
        return False, ", ".join(missing)
    return True, ""

_DEPS_OK, _MISSING_DEPS = _probe_deps()

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Research Intelligence",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Imports ──────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Root tokens ──────────────────────────────────────────────────────── */
:root {
    --bg:           #0f1117;
    --surface:      #181c27;
    --surface-2:    #1e2333;
    --border:       #2a3045;
    --border-light: #323a52;
    --accent:       #4f7cff;
    --accent-dim:   rgba(79,124,255,0.12);
    --accent-glow:  rgba(79,124,255,0.25);
    --success:      #22c55e;
    --success-dim:  rgba(34,197,94,0.12);
    --warn:         #f59e0b;
    --warn-dim:     rgba(245,158,11,0.12);
    --danger:       #ef4444;
    --text-primary: #e8ecf4;
    --text-secondary:#8b93a7;
    --text-muted:   #525a70;
    --mono:         'JetBrains Mono', monospace;
    --sans:         'Inter', sans-serif;
}

/* ── Reset & base ─────────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: var(--sans) !important;
    background-color: var(--bg) !important;
    color: var(--text-primary) !important;
}

.stApp {
    background-color: var(--bg);
}

/* ── Hide default chrome ──────────────────────────────────────────────── */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 2.5rem 3rem 4rem !important;
    max-width: 1100px !important;
}

/* ── Header bar ───────────────────────────────────────────────────────── */
.app-header {
    display: flex;
    align-items: baseline;
    gap: 14px;
    margin-bottom: 2.5rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--border);
}
.app-header .wordmark {
    font-size: 1.15rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--text-primary);
}
.app-header .badge {
    font-family: var(--mono);
    font-size: 0.68rem;
    font-weight: 500;
    color: var(--accent);
    background: var(--accent-dim);
    border: 1px solid rgba(79,124,255,0.3);
    padding: 2px 8px;
    border-radius: 3px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
.app-header .sub {
    margin-left: auto;
    font-size: 0.78rem;
    color: var(--text-muted);
    font-weight: 400;
}

/* ── Input section ────────────────────────────────────────────────────── */
.input-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.5rem;
}

.stTextInput > div > div > input {
    background-color: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    color: var(--text-primary) !important;
    font-family: var(--sans) !important;
    font-size: 0.95rem !important;
    padding: 0.75rem 1rem !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder {
    color: var(--text-muted) !important;
}

/* ── Button ───────────────────────────────────────────────────────────── */
.stButton > button {
    background-color: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: var(--sans) !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    padding: 0.65rem 1.6rem !important;
    height: auto !important;
    transition: background-color 0.15s ease, transform 0.1s ease !important;
    cursor: pointer;
}
.stButton > button:hover {
    background-color: #3d6aee !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}
.stButton > button:disabled {
    background-color: var(--border) !important;
    color: var(--text-muted) !important;
    cursor: not-allowed !important;
}

/* ── Pipeline tracker ─────────────────────────────────────────────────── */
.pipeline-track {
    display: flex;
    align-items: center;
    gap: 0;
    margin: 2rem 0 1.5rem;
    position: relative;
}
.pipeline-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
    position: relative;
}
.pipeline-step:not(:last-child)::after {
    content: '';
    position: absolute;
    top: 14px;
    left: 50%;
    width: 100%;
    height: 1px;
    background: var(--border);
    z-index: 0;
}
.pipeline-step.done:not(:last-child)::after {
    background: var(--accent);
}
.step-dot {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: var(--surface);
    border: 2px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1;
    font-family: var(--mono);
    font-size: 0.65rem;
    font-weight: 600;
    color: var(--text-muted);
    transition: all 0.2s ease;
}
.pipeline-step.active .step-dot {
    border-color: var(--accent);
    background: var(--accent-dim);
    color: var(--accent);
}
.pipeline-step.done .step-dot {
    border-color: var(--success);
    background: var(--success-dim);
    color: var(--success);
}
.step-label {
    margin-top: 6px;
    font-size: 0.68rem;
    font-weight: 500;
    color: var(--text-muted);
    letter-spacing: 0.04em;
    white-space: nowrap;
}
.pipeline-step.active .step-label { color: var(--accent); }
.pipeline-step.done .step-label   { color: var(--text-secondary); }

/* ── Cards ────────────────────────────────────────────────────────────── */
.result-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1rem;
}
.result-card.accent-left {
    border-left: 3px solid var(--accent);
}
.result-card.success-left {
    border-left: 3px solid var(--success);
}
.result-card.warn-left {
    border-left: 3px solid var(--warn);
}

.card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.85rem;
}
.card-title {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: var(--text-muted);
}
.card-body {
    font-size: 0.9rem;
    line-height: 1.75;
    color: var(--text-secondary);
    white-space: pre-wrap;
    word-break: break-word;
}

/* ── Score badge ──────────────────────────────────────────────────────── */
.score-pill {
    font-family: var(--mono);
    font-size: 0.75rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    display: inline-block;
}
.score-high   { background: var(--success-dim); color: var(--success); border: 1px solid rgba(34,197,94,0.3); }
.score-mid    { background: var(--warn-dim);    color: var(--warn);    border: 1px solid rgba(245,158,11,0.3); }
.score-low    { background: rgba(239,68,68,0.1);color: var(--danger);  border: 1px solid rgba(239,68,68,0.3); }

/* ── Status log ───────────────────────────────────────────────────────── */
.log-line {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 6px 0;
    border-bottom: 1px solid var(--border);
    font-family: var(--mono);
    font-size: 0.78rem;
    color: var(--text-secondary);
}
.log-line:last-child { border-bottom: none; }
.log-ts  { color: var(--text-muted); min-width: 60px; }
.log-tag { color: var(--accent); }
.log-tag.ok  { color: var(--success); }
.log-tag.err { color: var(--danger); }

/* ── Metric row ───────────────────────────────────────────────────────── */
.metric-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.metric-box {
    flex: 1;
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1rem 1.25rem;
}
.metric-box .m-label {
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    margin-bottom: 4px;
}
.metric-box .m-value {
    font-family: var(--mono);
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--text-primary);
}
.metric-box .m-sub {
    font-size: 0.72rem;
    color: var(--text-muted);
    margin-top: 2px;
}

/* ── Spinner override ─────────────────────────────────────────────────── */
.stSpinner > div {
    border-color: var(--accent) transparent transparent transparent !important;
}

/* ── Tabs ─────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-muted) !important;
    font-family: var(--sans) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    border-radius: 0 !important;
    padding: 0.55rem 1.1rem !important;
    border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
    color: var(--text-primary) !important;
    border-bottom-color: var(--accent) !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 1.5rem !important;
}

/* ── Expander ─────────────────────────────────────────────────────────── */
.streamlit-expanderHeader {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    color: var(--text-secondary) !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
}
.streamlit-expanderContent {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
    border-radius: 0 0 6px 6px !important;
}

/* ── Divider ──────────────────────────────────────────────────────────── */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 1.5rem 0 !important;
}

/* ── Scrollbar ────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border-light); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def ts():
    return time.strftime("%H:%M:%S")


def extract_score(feedback: str) -> tuple[int | None, str]:
    """Pull the numeric score out of the critic's output."""
    import re
    matches = re.findall(r'(\d{1,2})\s*/\s*10', feedback)
    if matches:
        score = int(matches[-1])
        if score >= 7:
            css = "score-high"
        elif score >= 5:
            css = "score-mid"
        else:
            css = "score-low"
        return score, css
    return None, ""


def render_header():
    st.markdown("""
    <div class="app-header">
        <span class="wordmark">Research Intelligence</span>
        <span class="badge">Multi-Agent</span>
        <span class="sub">Mistral · Tavily · LangChain</span>
    </div>
    """, unsafe_allow_html=True)
    if not _DEPS_OK:
        st.markdown(f"""
        <div style="
            background: var(--warn-dim);
            border: 1px solid rgba(245,158,11,0.35);
            border-left: 3px solid var(--warn);
            border-radius: 6px;
            padding: 0.7rem 1rem;
            margin-bottom: 1.5rem;
            font-size: 0.8rem;
            color: var(--text-secondary);
            line-height: 1.6;
        ">
            <strong style="color:var(--warn);font-size:0.72rem;letter-spacing:0.06em;text-transform:uppercase;">
                Demo mode
            </strong>
            &nbsp;&mdash;&nbsp;
            Missing packages: <code style="font-family:var(--mono);color:var(--warn);">{_MISSING_DEPS}</code>.
            Install them with
            <code style="font-family:var(--mono);color:var(--text-primary);">pip install {_MISSING_DEPS}</code>
            and restart Streamlit to connect the live pipeline.
            All UI features are fully functional with simulated output.
        </div>
        """, unsafe_allow_html=True)


def render_pipeline_tracker(active: int):
    """active: 0=idle, 1=search, 2=scrape, 3=write, 4=critique, 5=done"""
    steps = ["Search", "Scrape", "Write", "Critique"]

    def cls(i):
        idx = i + 1
        if active > idx:
            return "done"
        if active == idx:
            return "active"
        return ""

    def dot_content(i, c):
        if c == "done":
            return "&#10003;"
        return str(i + 1)

    html = '<div class="pipeline-track">'
    for i, label in enumerate(steps):
        c = cls(i)
        html += f"""
        <div class="pipeline-step {c}">
            <div class="step-dot">{dot_content(i, c)}</div>
            <span class="step-label">{label}</span>
        </div>"""
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_log(entries: list[tuple[str, str, str]]):
    """entries: list of (timestamp, tag, message)"""
    html = ""
    for t, tag, msg in entries:
        tag_cls = "ok" if tag in ("DONE", "OK") else ("err" if tag == "ERR" else "")
        html += f"""
        <div class="log-line">
            <span class="log-ts">{t}</span>
            <span class="log-tag {tag_cls}">[{tag}]</span>
            <span>{msg}</span>
        </div>"""
    if html:
        st.markdown(f'<div class="result-card">{html}</div>', unsafe_allow_html=True)


# ── Mock pipeline (runs when real deps are absent) ────────────────────────────

def _mock_pipeline(topic: str) -> dict:
    """Simulates the full pipeline with realistic placeholder data."""
    time.sleep(0.4)   # search
    search_results = textwrap.dedent(f"""\
        Title : {topic} — Overview and Recent Developments
        URL   : https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}
        Snippet: {topic} has seen significant progress over the past several years,
        driven by advances in computational methods and interdisciplinary research.

        ----
        Title : Latest Research on {topic} | Nature
        URL   : https://www.nature.com/search?q={topic.replace(' ', '+')}
        Snippet: Peer-reviewed studies highlight key breakthroughs and ongoing
        challenges in the field of {topic}.

        ----
        Title : {topic} — Stanford Encyclopedia
        URL   : https://plato.stanford.edu/entries/{topic.lower().replace(' ', '-')}/
        Snippet: A comprehensive academic treatment of {topic}, covering foundational
        theory, current debates, and future directions.
    """)

    time.sleep(0.3)   # scrape
    scrape_content = textwrap.dedent(f"""\
        [Scraped from Wikipedia — {topic}]

        {topic} refers to a broad area of inquiry with roots in multiple scientific
        disciplines. Over the past decade, rapid progress has been made possible by
        increased computational power, large-scale datasets, and novel theoretical
        frameworks.

        Key contributors include research groups at MIT, Stanford, Oxford, and
        several national laboratories. Landmark publications in Nature and Science
        have documented significant milestones, while preprint servers such as
        arXiv have accelerated dissemination of new results.

        Current open problems include scalability, interpretability, and the
        integration of domain knowledge into data-driven models. International
        consortia are coordinating multi-site studies to address these challenges
        at scale.
    """)

    time.sleep(0.5)   # write
    report = textwrap.dedent(f"""\
        RESEARCH REPORT: {topic.upper()}
        {'=' * 60}

        INTRODUCTION
        ------------
        {topic} represents one of the most actively studied areas in contemporary
        science and engineering. This report synthesises recent findings from
        primary literature, encyclopaedic sources, and curated web resources to
        provide a structured overview of the field.

        KEY FINDINGS
        ------------
        1. Accelerating progress: Publication volume in {topic} has grown at
           roughly 25% per year over the last five years, with the majority of
           high-impact work appearing in top-tier journals and conferences.

        2. Interdisciplinary convergence: Advances in {topic} are increasingly
           driven by cross-domain collaboration, combining methods from computer
           science, mathematics, and domain-specific sciences.

        3. Infrastructure investment: Major funding bodies — including NIH, NSF,
           DARPA, and equivalents in the EU and Asia — have significantly increased
           grants targeting {topic}, reflecting its perceived strategic importance.

        4. Open challenges: Despite progress, reproducibility, generalisation
           beyond benchmark datasets, and ethical deployment remain critical
           concerns that the community is actively working to resolve.

        5. Emerging sub-fields: Novel sub-areas within {topic} are emerging at a
           rapid pace, with several expected to become independent research domains
           within the next five years.

        CONCLUSION
        ----------
        {topic} is a maturing field with significant momentum. Near-term prospects
        are strong, contingent on the community's ability to address fundamental
        challenges in reliability and interpretability. Cross-sector collaboration
        and open data sharing will be critical enablers of continued progress.

        SOURCES
        -------
        - https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}
        - https://www.nature.com/search?q={topic.replace(' ', '+')}
        - https://plato.stanford.edu/entries/{topic.lower().replace(' ', '-')}/
    """)

    time.sleep(0.4)   # critique
    feedback = textwrap.dedent(f"""\
        CRITIC AGENT REVIEW — {topic.upper()}
        {'=' * 60}

        EVALUATION
        ----------
        1. Accuracy and factual consistency  : The report is grounded in verifiable
           sources and makes no claims unsupported by the cited material.  [Good]

        2. Completeness of information       : Core dimensions are covered well.
           A deeper dive into quantitative metrics (publication counts, funding
           figures) would strengthen the findings section.  [Adequate]

        3. Logical structure and organisation: The Introduction → Key Findings →
           Conclusion arc is clear and easy to follow.  [Strong]

        4. Clarity and readability           : Language is precise and accessible
           to a technically literate audience without unnecessary jargon.  [Strong]

        5. Use of evidence and supporting details: Three primary sources are cited.
           Adding two or three further peer-reviewed references would raise
           credibility.  [Adequate]

        6. Missing topics or weak sections   : The report does not address
           geographical distribution of research activity or recent regulatory
           developments that may affect the field.  [Gap identified]

        7. Overall quality score             : 7/10

        STRENGTHS
        ---------
        - Well-organised narrative with clear section boundaries.
        - Balanced treatment of progress and open challenges.
        - Sources are reputable and directly relevant.

        WEAKNESSES
        ----------
        - Limited quantitative depth in the Key Findings section.
        - Only three sources cited; broader literature review recommended.
        - Regulatory and geopolitical context is absent.

        SPECIFIC IMPROVEMENTS
        ---------------------
        - Add at least two peer-reviewed journal articles to the source list.
        - Include a data table summarising funding or publication trends.
        - Expand the conclusion to address policy implications.

        FINAL SCORE: 7/10
    """)

    return {
        "search_results": search_results,
        "scrape_content": scrape_content,
        "report":         report,
        "feedback":       feedback,
    }


# ── Pipeline runner ───────────────────────────────────────────────────────────

def run_pipeline(topic: str) -> tuple[dict | None, str | None]:
    """
    Uses the real pipeline when all dependencies are available.
    Falls back to the mock pipeline transparently when they are not.
    """
    if not _DEPS_OK:
        return _mock_pipeline(topic), None
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from pipeline import run_research_pipeline
        return run_research_pipeline(topic), None
    except Exception as e:
        return None, str(e)


# ── Main app ──────────────────────────────────────────────────────────────────

def main():
    render_header()

    # ── Session state init ────────────────────────────────────────────────────
    defaults = {
        "result": None, "error": None, "log": [], "running": False,
        "elapsed": 0, "topic_snapshot": "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    # ── Input row ─────────────────────────────────────────────────────────────
    st.markdown('<div class="input-label">Research topic</div>', unsafe_allow_html=True)
    col_input, col_btn = st.columns([5, 1], gap="small")
    with col_input:
        topic = st.text_input(
            label="topic",
            label_visibility="collapsed",
            placeholder="e.g. Advances in quantum error correction 2024",
            key="topic_input",
            disabled=st.session_state.running,
        )
    with col_btn:
        run_btn = st.button(
            "Run pipeline",
            disabled=st.session_state.running or not (topic or "").strip(),
            use_container_width=True,
        )

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Pipeline execution ────────────────────────────────────────────────────
    if run_btn and topic.strip():
        st.session_state.running        = True
        st.session_state.result         = None
        st.session_state.error          = None
        st.session_state.log            = []
        st.session_state.elapsed        = 0
        st.session_state.topic_snapshot = topic.strip()
        st.rerun()

    if st.session_state.running:
        tracker_placeholder = st.empty()
        status_placeholder  = st.empty()
        log_placeholder     = st.empty()

        log = st.session_state.log

        def push_log(tag, msg):
            log.append((ts(), tag, msg))
            with log_placeholder:
                render_log(log)

        def set_step(step: int, status_msg: str):
            with tracker_placeholder:
                render_pipeline_tracker(step)
            status_placeholder.markdown(
                f'<div style="color:var(--text-muted);font-size:0.82rem;margin-bottom:0.5rem">{status_msg}</div>',
                unsafe_allow_html=True,
            )

        t0 = time.time()
        mode_tag = "MOCK" if not _DEPS_OK else "RUN"

        try:
            set_step(1, "Dispatching web search agent...")
            push_log(mode_tag, f"Pipeline started — topic: \"{st.session_state.topic_snapshot}\"")
            push_log("SEARCH", "Search agent invoked via Tavily" if _DEPS_OK else "Search agent invoked (simulated)")

            result, err = run_pipeline(st.session_state.topic_snapshot)

            if err:
                raise RuntimeError(err)

            push_log("OK", "Search results retrieved")
            set_step(2, "Reader agent scraping top source...")
            push_log("SCRAPE", "URL selected and scraped" if _DEPS_OK else "URL selected and scraped (simulated)")

            set_step(3, "Writer agent generating report...")
            push_log("WRITE", "Mistral writer invoked" if _DEPS_OK else "Writer agent invoked (simulated)")

            set_step(4, "Critic agent reviewing report...")
            push_log("CRITIC", "Critic agent invoked" if _DEPS_OK else "Critic agent invoked (simulated)")

            elapsed = round(time.time() - t0, 1)
            set_step(5, "")
            push_log("DONE", f"Pipeline complete in {elapsed}s")
            status_placeholder.empty()

            st.session_state.result  = result
            st.session_state.log     = log
            st.session_state.elapsed = elapsed

        except Exception as e:
            push_log("ERR", str(e))
            st.session_state.error = str(e)
        finally:
            st.session_state.running = False
            st.rerun()

    # ── Idle or error state ───────────────────────────────────────────────────
    if not st.session_state.running and st.session_state.result is None and st.session_state.error is None:
        render_pipeline_tracker(0)
        st.markdown("""
        <div class="result-card" style="text-align:center;padding:3rem 2rem;">
            <div style="font-size:0.82rem;color:var(--text-muted);line-height:1.8;">
                Enter a research topic above and run the pipeline.<br>
                The system will search the web, scrape a source, write a structured report,<br>
                and produce a scored critique — end to end.
            </div>
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.error:
        render_pipeline_tracker(0)
        st.markdown(f"""
        <div class="result-card" style="border-left:3px solid var(--danger);">
            <div class="card-header"><span class="card-title">Pipeline error</span></div>
            <div class="card-body" style="color:var(--danger);font-family:var(--mono);font-size:0.8rem;">{st.session_state.error}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.session_state.log:
            render_log(st.session_state.log)

    # ── Results ───────────────────────────────────────────────────────────────
    if st.session_state.result:
        result = st.session_state.result
        render_pipeline_tracker(5)

        # Metric summary row
        score, score_css = extract_score(result.get("feedback", ""))
        report_words = len(result.get("report", "").split())
        search_chars = len(result.get("search_results", ""))

        score_display = f"{score}/10" if score is not None else "N/A"
        score_color   = (
            "var(--success)" if score_css == "score-high"
            else "var(--warn)" if score_css == "score-mid"
            else "var(--danger)" if score_css == "score-low"
            else "var(--text-secondary)"
        )

        st.markdown(f"""
        <div class="metric-row">
            <div class="metric-box">
                <div class="m-label">Quality score</div>
                <div class="m-value" style="color:{score_color};">{score_display}</div>
                <div class="m-sub">out of 10 by critic agent</div>
            </div>
            <div class="metric-box">
                <div class="m-label">Report length</div>
                <div class="m-value">{report_words:,}</div>
                <div class="m-sub">words in final report</div>
            </div>
            <div class="metric-box">
                <div class="m-label">Search data</div>
                <div class="m-value">{search_chars:,}</div>
                <div class="m-sub">characters retrieved</div>
            </div>
            <div class="metric-box">
                <div class="m-label">Run time</div>
                <div class="m-value">{st.session_state.elapsed}s</div>
                <div class="m-sub">end-to-end pipeline</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Tabs: Report / Critique / Raw
        tab_report, tab_critique, tab_raw = st.tabs(["Report", "Critique", "Raw data"])

        with tab_report:
            report_text = result.get("report", "No report generated.")
            st.markdown(f"""
            <div class="result-card accent-left">
                <div class="card-header">
                    <span class="card-title">Generated report</span>
                </div>
                <div class="card-body">{report_text}</div>
            </div>
            """, unsafe_allow_html=True)

        with tab_critique:
            feedback_text = result.get("feedback", "No critique available.")
            score, score_css = extract_score(feedback_text)
            score_badge = (
                f'<span class="score-pill {score_css}">{score}/10</span>'
                if score is not None else ""
            )
            st.markdown(f"""
            <div class="result-card success-left">
                <div class="card-header">
                    <span class="card-title">Critic agent feedback</span>
                    {score_badge}
                </div>
                <div class="card-body">{feedback_text}</div>
            </div>
            """, unsafe_allow_html=True)

        with tab_raw:
            with st.expander("Search results", expanded=False):
                st.markdown(f"""
                <div class="card-body" style="font-family:var(--mono);font-size:0.78rem;">
                    {result.get('search_results', 'None')}
                </div>""", unsafe_allow_html=True)

            with st.expander("Scraped content", expanded=False):
                st.markdown(f"""
                <div class="card-body" style="font-family:var(--mono);font-size:0.78rem;">
                    {result.get('scrape_content', 'None')}
                </div>""", unsafe_allow_html=True)

        # Execution log
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div class="input-label">Execution log</div>', unsafe_allow_html=True)
        render_log(st.session_state.log)

        # Re-run
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("New research run", use_container_width=False):
            for k, v in {"result": None, "error": None, "log": [], "elapsed": 0, "topic_snapshot": ""}.items():
                st.session_state[k] = v
            st.rerun()


if __name__ == "__main__":
    main()
