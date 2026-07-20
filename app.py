"""Inkprint — an AI blog writing agent powered by DigitalOcean and Memori."""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import uuid

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from agents import (
    AgentError,
    ContentGenerator,
    DigitalOceanAgent,
    DocumentProcessor,
    GeneratedArticle,
    GenerationRequest,
    ProcessedDocument,
    StyleAnalyzer,
    StyleProfile,
)
from memory import MemoryStore, article_to_html

load_dotenv()

st.set_page_config(
    page_title="Inkprint · AI Blog Writing Agent",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": "https://github.com/tirth1263/blog-writing-agent#readme",
        "Report a bug": "https://github.com/tirth1263/blog-writing-agent/issues",
        "About": "Inkprint learns the patterns that make your writing unmistakably yours.",
    },
)


APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

:root {
  --ink: #17241d;
  --muted: #66736b;
  --line: #dfe7e1;
  --paper: #f8faf7;
  --card: #ffffff;
  --lime: #b9ef69;
  --lime-dark: #84bd33;
  --forest: #1d4935;
  --blue: #82b7ff;
  --peach: #ffb990;
}

html, body, [class*="css"], [data-testid="stAppViewContainer"] {
  font-family: 'DM Sans', sans-serif;
  color: var(--ink);
}

[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(circle at 75% -10%, rgba(185,239,105,.18), transparent 26rem),
    #f8faf7;
}

[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"] { max-width: 1240px; padding-top: 1.2rem; }

[data-testid="stSidebar"] {
  background: #17241d;
  border-right: 0;
}
[data-testid="stSidebar"] * { color: #f6f9f5; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
[data-testid="stSidebar"] .stMarkdown p { color: #b8c5bc; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.1); }
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
  background: rgba(255,255,255,.06);
  border: 1px dashed rgba(255,255,255,.22);
  border-radius: 16px;
}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {
  color: #17241d;
  background: var(--lime);
}
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] input {
  background: rgba(255,255,255,.08) !important;
  color: white !important;
  border-color: rgba(255,255,255,.12) !important;
}

h1, h2, h3, .brand-word { font-family: 'Manrope', sans-serif; letter-spacing: -.035em; }

.brand-lockup { display:flex; align-items:center; gap:.7rem; padding:.15rem 0 1.1rem; }
.brand-mark { width:38px; height:38px; border-radius:12px; background:var(--lime); color:#17321f;
  display:grid; place-items:center; font-size:20px; font-weight:800; box-shadow:0 8px 25px rgba(185,239,105,.15); }
.brand-word { font-weight:800; font-size:1.3rem; color:#fff; }
.brand-tag { font-size:.69rem; letter-spacing:.12em; text-transform:uppercase; color:#8da095; font-weight:700; }

.step-label { display:flex; align-items:center; gap:.65rem; margin:1.2rem 0 .6rem; }
.step-no { width:26px; height:26px; display:grid; place-items:center; border-radius:50%; background:rgba(185,239,105,.13);
  color:var(--lime); font-size:.74rem; font-weight:800; border:1px solid rgba(185,239,105,.2); }
.step-title { color:#f4f8f4; font-weight:700; font-size:.91rem; }

.mode-chip { display:inline-flex; align-items:center; gap:.4rem; font-size:.73rem; padding:.4rem .65rem; border-radius:999px;
  background:rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.1); color:#c5d2c9; margin:.4rem 0; }
.mode-dot { width:7px; height:7px; border-radius:50%; background:var(--lime); box-shadow:0 0 0 4px rgba(185,239,105,.1); }
.privacy-note { border:1px solid rgba(255,255,255,.08); background:rgba(255,255,255,.035); padding:.75rem .85rem;
  border-radius:12px; font-size:.73rem; color:#9fb0a5; line-height:1.5; margin-top:1rem; }

.hero {
  position:relative; overflow:hidden; min-height:260px; border:1px solid var(--line); border-radius:28px;
  padding:2.4rem 2.7rem; background:#fff; box-shadow:0 18px 60px rgba(29,73,53,.07); margin-bottom:1.3rem;
}
.hero:after { content:""; position:absolute; width:310px; height:310px; border-radius:50%; right:-85px; top:-130px;
  background:var(--lime); opacity:.85; }
.hero:before { content:"✦"; position:absolute; right:104px; top:58px; z-index:2; font-size:5.2rem; color:#244e39; transform:rotate(12deg); }
.eyebrow { display:inline-flex; gap:.45rem; align-items:center; text-transform:uppercase; letter-spacing:.13em; font-weight:800;
  font-size:.72rem; color:#47705b; margin-bottom:.8rem; }
.eyebrow span { width:20px; height:2px; background:var(--lime-dark); display:inline-block; }
.hero h1 { margin:0; max-width:780px; font-size:clamp(2.25rem,4.4vw,4.15rem); line-height:1.01; color:var(--ink); }
.hero h1 em { color:#4f7d63; font-style:normal; }
.hero p { max-width:650px; color:var(--muted); font-size:1.05rem; line-height:1.65; margin:1.1rem 0 0; }

.status-row { display:flex; gap:.6rem; flex-wrap:wrap; margin-bottom:1.1rem; }
.status-pill { display:inline-flex; align-items:center; gap:.48rem; border:1px solid var(--line); background:#fff; border-radius:999px;
  padding:.48rem .72rem; color:#536159; font-size:.77rem; font-weight:600; }
.status-pill b { width:7px; height:7px; border-radius:50%; display:inline-block; background:#9aa69e; }
.status-pill.live b { background:#72b829; box-shadow:0 0 0 4px rgba(114,184,41,.1); }

.section-kicker { color:#789082; letter-spacing:.13em; text-transform:uppercase; font-size:.69rem; font-weight:800; margin-bottom:.15rem; }
.section-title { font-family:'Manrope',sans-serif; font-size:1.45rem; font-weight:750; letter-spacing:-.035em; color:var(--ink); margin-bottom:.2rem; }
.section-copy { color:var(--muted); font-size:.88rem; margin-bottom:1rem; }

.metric-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:.7rem; margin:.6rem 0 1.2rem; }
.metric-card { background:#fff; border:1px solid var(--line); border-radius:15px; padding:.85rem; }
.metric-value { font:700 1.25rem 'Manrope',sans-serif; color:var(--ink); }
.metric-label { color:#829087; font-size:.7rem; text-transform:uppercase; letter-spacing:.08em; margin-top:.2rem; }

.profile-card { border:1px solid rgba(185,239,105,.23); background:rgba(185,239,105,.075); border-radius:15px;
  padding:.8rem .9rem; margin:.45rem 0; }
.profile-card small { display:block; text-transform:uppercase; letter-spacing:.09em; color:#9eb0a4; font-weight:800; font-size:.62rem; margin-bottom:.3rem; }
.profile-card div { color:#eff7f0; font-size:.78rem; line-height:1.45; }

.article-shell { background:#fff; border:1px solid var(--line); border-radius:22px; padding:clamp(1.3rem,4vw,3rem);
  box-shadow:0 14px 50px rgba(29,73,53,.06); margin-top:1rem; }
.article-meta { display:flex; flex-wrap:wrap; gap:.5rem; border-bottom:1px solid #edf1ed; padding-bottom:1rem; margin-bottom:1.4rem; }
.article-meta span { font-size:.73rem; font-weight:700; color:#637269; border:1px solid #e1e8e2; padding:.32rem .55rem; border-radius:999px; }

.empty-state { text-align:center; background:#fff; border:1px dashed #ced8d0; border-radius:22px; padding:3.2rem 1.2rem; }
.empty-icon { width:58px; height:58px; border-radius:18px; background:#eff9df; display:grid; place-items:center; margin:0 auto 1rem;
  font-size:1.6rem; color:#568426; }
.empty-state h3 { margin:0; color:var(--ink); }
.empty-state p { color:var(--muted); max-width:470px; margin:.55rem auto 0; }

.library-card { background:#fff; border:1px solid var(--line); border-radius:18px; padding:1rem 1.15rem; margin:.7rem 0; }
.library-card h4 { margin:0 0 .35rem; color:var(--ink); font:700 1.05rem 'Manrope',sans-serif; }
.library-card p { color:var(--muted); font-size:.82rem; margin:0; }
.library-meta { color:#8a978f; font-size:.68rem; margin-top:.7rem; text-transform:uppercase; letter-spacing:.06em; }

.feature-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:.9rem; margin-top:1rem; }
.feature { background:#fff; border:1px solid var(--line); border-radius:18px; padding:1.1rem; }
.feature-icon { width:36px; height:36px; border-radius:11px; display:grid; place-items:center; background:#eef8df; margin-bottom:.8rem; }
.feature h4 { font:700 .96rem 'Manrope',sans-serif; margin:0 0 .35rem; }
.feature p { color:var(--muted); font-size:.79rem; line-height:1.5; margin:0; }

div[data-testid="stButton"] button, div[data-testid="stDownloadButton"] button {
  border-radius:12px; font-weight:700; min-height:2.65rem; border-color:#d9e2da;
}
div[data-testid="stButton"] button[kind="primary"] { background:var(--forest); border-color:var(--forest); color:#fff; }
div[data-testid="stButton"] button[kind="primary"]:hover { background:#286347; border-color:#286347; }
[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"] { background:var(--lime); color:#18281e; border-color:var(--lime); }

[data-baseweb="tab-list"] { gap:.3rem; background:#eef2ee; border-radius:13px; padding:.25rem; width:fit-content; }
[data-baseweb="tab"] { border-radius:10px; padding:.45rem 1rem; }
[aria-selected="true"][data-baseweb="tab"] { background:#fff; box-shadow:0 2px 9px rgba(30,50,38,.08); }

div[data-testid="stForm"] { background:#fff; border:1px solid var(--line); border-radius:20px; padding:1.1rem 1.2rem 1.25rem; }
div[data-testid="stTextArea"] textarea, div[data-testid="stTextInput"] input,
div[data-baseweb="select"] > div { border-radius:11px; border-color:#dce5de; background:#fbfcfa; }

@media (max-width: 760px) {
  .hero { padding:1.5rem; min-height:auto; }
  .hero:after,.hero:before { display:none; }
  .metric-grid,.feature-grid { grid-template-columns:1fr; }
  [data-testid="stMainBlockContainer"] { padding-left:1rem; padding-right:1rem; }
}
</style>
"""

st.markdown(APP_CSS, unsafe_allow_html=True)


def setting(name: str, default: str = "") -> str:
    """Read a setting from Streamlit secrets or environment without raising."""
    try:
        value = st.secrets.get(name, os.getenv(name, default))
    except Exception:
        value = os.getenv(name, default)
    return str(value or "")


@st.cache_resource
def get_store() -> MemoryStore:
    return MemoryStore(setting("DATABASE_PATH", ".data/blog_agent.db"))


def init_state() -> None:
    defaults = {
        "session_id": uuid.uuid4().hex[:12],
        "profile": None,
        "documents": [],
        "current_article": None,
        "article_saved": False,
        "session_endpoint": "",
        "session_access_key": "",
        "session_memori_key": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def user_id() -> str:
    seed = setting("APP_USER_ID", st.session_state.session_id)
    return "writer-" + hashlib.sha256(seed.encode()).hexdigest()[:16]


def get_agent() -> DigitalOceanAgent:
    endpoint = st.session_state.session_endpoint or setting("DIGITAL_OCEAN_ENDPOINT")
    access_key = st.session_state.session_access_key or setting("DIGITAL_OCEAN_AGENT_ACCESS_KEY")
    memori_key = st.session_state.session_memori_key or setting("MEMORI_API_KEY")
    return DigitalOceanAgent(
        endpoint,
        access_key,
        entity_id=user_id(),
        memori_api_key=memori_key,
    )


def safe_store() -> MemoryStore | None:
    try:
        return get_store()
    except Exception:
        return None


def copy_button(text: str, key: str) -> None:
    payload = json.dumps(text).replace("<", "\\u003c")
    components.html(
        f"""
        <button id="copy-{key}" onclick='copyText()' style="width:100%;height:42px;border:1px solid #d9e2da;
        border-radius:12px;background:white;color:#26372d;font:700 14px Arial;cursor:pointer">Copy markdown</button>
        <script>
        async function copyText() {{
          await navigator.clipboard.writeText({payload});
          const b=document.getElementById('copy-{key}'); b.textContent='Copied ✓';
          setTimeout(()=>b.textContent='Copy markdown',1600);
        }}
        </script>""",
        height=48,
    )


def render_profile(profile: StyleProfile) -> None:
    st.markdown(
        f"""<div class="metric-grid">
          <div class="metric-card"><div class="metric-value">{profile.average_sentence_length:g}</div><div class="metric-label">Words / sentence</div></div>
          <div class="metric-card"><div class="metric-value">{profile.readability_score:g}</div><div class="metric-label">Readability</div></div>
          <div class="metric-card"><div class="metric-value">{profile.source_word_count:,}</div><div class="metric-label">Words learned</div></div>
        </div>""",
        unsafe_allow_html=True,
    )
    for label, value in (
        ("Tone", profile.tone),
        ("Voice", profile.voice),
        ("Structure", profile.structure),
        ("Vocabulary", profile.vocabulary),
        ("Sentence rhythm", profile.sentence_patterns),
    ):
        st.markdown(
            f'<div class="profile-card"><small>{html.escape(label)}</small><div>{html.escape(value)}</div></div>',
            unsafe_allow_html=True,
        )
    if profile.signature_traits:
        st.caption("Signature traits · " + "  ·  ".join(profile.signature_traits))


def sidebar(agent: DigitalOceanAgent) -> None:
    with st.sidebar:
        st.markdown(
            """<div class="brand-lockup"><div class="brand-mark">✦</div><div>
            <div class="brand-word">Inkprint</div><div class="brand-tag">Writing intelligence</div>
            </div></div>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="mode-chip"><span class="mode-dot"></span>{"DigitalOcean AI connected" if agent.configured else "Private demo mode"}</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="step-label"><span class="step-no">1</span><span class="step-title">Teach your style</span></div>',
            unsafe_allow_html=True,
        )
        uploaded = st.file_uploader(
            "Upload your best writing",
            type=["pdf", "docx", "txt", "md"],
            accept_multiple_files=True,
            label_visibility="collapsed",
            help="Documents are extracted in memory and source files are never saved.",
        )
        if uploaded:
            total_kb = sum(item.size for item in uploaded) / 1024
            st.caption(f"{len(uploaded)} file{'s' if len(uploaded) != 1 else ''} ready · {total_kb:,.0f} KB")
        analyze = st.button(
            "✦  Analyze writing style",
            type="primary",
            use_container_width=True,
            disabled=not uploaded,
        )
        if analyze:
            processor = DocumentProcessor()
            processed: list[ProcessedDocument] = []
            errors: list[str] = []
            with st.spinner("Finding the patterns that make your writing yours…"):
                for item in uploaded:
                    try:
                        item.seek(0)
                        processed.append(processor.process(item))
                    except ValueError as exc:
                        errors.append(str(exc))
                if processed:
                    try:
                        profile = StyleAnalyzer(agent).analyze(processed)
                        st.session_state.documents = processed
                        st.session_state.profile = profile
                        store = safe_store()
                        if store:
                            store.save_profile(user_id(), profile)
                        st.success("Your style fingerprint is ready.")
                    except (ValueError, AgentError) as exc:
                        st.error(str(exc))
            for error in errors:
                st.warning(error)

        st.markdown(
            '<div class="step-label"><span class="step-no">2</span><span class="step-title">Your style fingerprint</span></div>',
            unsafe_allow_html=True,
        )
        profile = st.session_state.profile
        if profile:
            render_profile(profile)
        else:
            st.caption(
                "Upload an article to reveal your tone, voice, structure, vocabulary, and sentence rhythm."
            )

        st.markdown(
            '<div class="step-label"><span class="step-no">3</span><span class="step-title">Memory & configuration</span></div>',
            unsafe_allow_html=True,
        )
        with st.expander("Connect your own AI", expanded=False):
            st.caption("Credentials stay in this browser session and are never written to the database.")
            endpoint_value = st.text_input(
                "DigitalOcean agent endpoint",
                value=st.session_state.session_endpoint,
                placeholder="https://…agents.do-ai.run",
            )
            key_value = st.text_input(
                "Agent access key",
                value=st.session_state.session_access_key,
                type="password",
            )
            memori_value = st.text_input(
                "Memori API key (optional)",
                value=st.session_state.session_memori_key,
                type="password",
            )
            if st.button("Use this configuration", use_container_width=True):
                st.session_state.session_endpoint = endpoint_value.strip()
                st.session_state.session_access_key = key_value.strip()
                st.session_state.session_memori_key = memori_value.strip()
                st.rerun()
        if agent.memory_enabled:
            st.caption("✓ Memori is learning from this writing session")
        elif agent.configured:
            st.caption("DigitalOcean connected · add Memori for long-term recall")
        st.markdown(
            '<div class="privacy-note">🔒 Source files are processed in memory and never stored. Only the resulting style profile and articles enter the local library.</div>',
            unsafe_allow_html=True,
        )


def writer_tab(agent: DigitalOceanAgent) -> None:
    st.markdown(
        '<div class="section-kicker">Writing studio</div><div class="section-title">Turn an idea into a finished draft</div><div class="section-copy">Give the agent a topic and a little direction. Your style profile does the rest.</div>',
        unsafe_allow_html=True,
    )
    with st.form("generation_form", clear_on_submit=False):
        topic = st.text_area(
            "What do you want to write about?",
            height=108,
            placeholder="e.g. Write a practical guide to building healthy remote-work habits…",
        )
        col1, col2 = st.columns(2)
        with col1:
            article_type = st.selectbox(
                "Format",
                [
                    "How-to guide",
                    "Thought leadership",
                    "Listicle",
                    "Explainer",
                    "Opinion essay",
                    "Case study",
                ],
            )
            audience = st.text_input("Audience", value="Curious professionals")
        with col2:
            length = st.selectbox(
                "Length",
                ["Medium · 800–1,000 words", "Short · 400–600 words", "Long · 1,300–1,600 words"],
            )
            keyword_text = st.text_input(
                "Keywords (optional)", placeholder="AI strategy, productivity, teams"
            )
        instructions = st.text_input(
            "Extra direction (optional)",
            placeholder="Include a real-world example and end with a 3-step checklist",
        )
        submitted = st.form_submit_button("Generate in my voice  →", type="primary", use_container_width=True)

    if submitted:
        request = GenerationRequest(
            topic=topic,
            audience=audience,
            article_type=article_type,
            length=length,
            keywords=[part.strip() for part in keyword_text.split(",") if part.strip()],
            instructions=instructions,
        )
        try:
            with st.spinner("Shaping the argument, matching your rhythm, polishing the draft…"):
                article = ContentGenerator(agent).generate(request, st.session_state.profile)
            st.session_state.current_article = article
            st.session_state.article_saved = False
        except (ValueError, AgentError) as exc:
            st.error(str(exc))

    article: GeneratedArticle | None = st.session_state.current_article
    if not article:
        st.markdown(
            """<div class="empty-state"><div class="empty-icon">✎</div><h3>Your next draft starts here</h3>
            <p>Describe an idea above. Inkprint will structure it, match your writing fingerprint, and return clean Markdown ready to publish.</p></div>""",
            unsafe_allow_html=True,
        )
        return

    st.markdown('<div class="article-shell">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="article-meta"><span>{article.word_count:,} words</span><span>{html.escape(article.mode)}</span><span>Markdown</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(article.content)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("#### Take it with you")
    action1, action2, action3, action4 = st.columns(4)
    slug = re.sub(r"[^a-z0-9]+", "-", article.title.lower()).strip("-")[:70] or "article"
    with action1:
        copy_button(article.content, "current")
    with action2:
        st.download_button(
            "Download .md",
            article.content,
            file_name=f"{slug}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with action3:
        st.download_button(
            "Download .html",
            article_to_html(article),
            file_name=f"{slug}.html",
            mime="text/html",
            use_container_width=True,
        )
    with action4:
        save_label = "Saved ✓" if st.session_state.article_saved else "Save to library"
        if st.button(save_label, use_container_width=True, disabled=st.session_state.article_saved):
            store = safe_store()
            if store:
                store.save_article(user_id(), article)
                st.session_state.article_saved = True
                st.rerun()
            else:
                st.error("The article library is unavailable in this environment.")

    with st.expander("Copy-ready Markdown"):
        st.code(article.content, language="markdown")


def library_tab() -> None:
    st.markdown(
        '<div class="section-kicker">Content library</div><div class="section-title">The work worth keeping</div><div class="section-copy">Saved drafts stay on this deployment until you remove them.</div>',
        unsafe_allow_html=True,
    )
    store = safe_store()
    articles = store.list_articles(user_id()) if store else []
    if not articles:
        st.markdown(
            """<div class="empty-state"><div class="empty-icon">▤</div><h3>No saved drafts yet</h3>
            <p>Generate an article in the Writing Studio, then save it here for quick access and export.</p></div>""",
            unsafe_allow_html=True,
        )
        return
    for item in articles:
        date = item["created_at"][:10]
        st.markdown(
            f"""<div class="library-card"><h4>{html.escape(item["title"])}</h4>
            <p>{html.escape(item["excerpt"])}</p><div class="library-meta">{item["word_count"]:,} words · {html.escape(item["mode"])} · {date}</div></div>""",
            unsafe_allow_html=True,
        )
        with st.expander(f"Open · {item['title']}"):
            st.markdown(item["content"])
            dl, delete = st.columns([3, 1])
            with dl:
                st.download_button(
                    "Download Markdown",
                    item["content"],
                    file_name=f"article-{item['id']}.md",
                    mime="text/markdown",
                    key=f"download-{item['id']}",
                    use_container_width=True,
                )
            with delete:
                if st.button("Delete", key=f"delete-{item['id']}", use_container_width=True):
                    store.delete_article(user_id(), int(item["id"]))
                    st.rerun()


def about_tab() -> None:
    st.markdown(
        '<div class="section-kicker">How it works</div><div class="section-title">Your voice, translated into a writing system</div><div class="section-copy">Two focused agents work together, with memory connecting every session.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """<div class="feature-grid">
          <div class="feature"><div class="feature-icon">⌁</div><h4>1 · Read locally</h4><p>PDF, DOCX, TXT, and Markdown files are extracted in memory. The original documents are never saved.</p></div>
          <div class="feature"><div class="feature-icon">◌</div><h4>2 · Build a fingerprint</h4><p>The Knowledge Agent measures tone, voice, rhythm, structure, vocabulary, and signature habits.</p></div>
          <div class="feature"><div class="feature-icon">✦</div><h4>3 · Write with memory</h4><p>The Writing Agent combines your fingerprint with each brief. Memori carries useful context across sessions.</p></div>
        </div>""",
        unsafe_allow_html=True,
    )
    st.markdown("### What the analysis notices")
    a, b = st.columns(2)
    with a:
        st.markdown(
            """
- **Tone and voice** — how you build authority and relate to readers
- **Sentence rhythm** — average length, variance, and pacing
- **Structure** — paragraph density, transitions, and idea progression
"""
        )
    with b:
        st.markdown(
            """
- **Vocabulary** — complexity, recurring language, and jargon preference
- **Example style** — scenarios, analogies, evidence, and practical detail
- **Signature traits** — the habits that make the writing recognizably yours
"""
        )
    st.info(
        "No API keys? No problem. Demo mode performs local linguistic analysis and produces a representative draft. "
        "Connect DigitalOcean AI for full generation and Memori for long-term conversation memory."
    )


def main() -> None:
    init_state()
    store = safe_store()
    if st.session_state.profile is None and store:
        st.session_state.profile = store.latest_profile(user_id())

    try:
        agent = get_agent()
    except AgentError as exc:
        agent = DigitalOceanAgent(None, None)
        st.warning(str(exc))
    sidebar(agent)

    st.markdown(
        """<div class="status-row"><div class="status-pill live"><b></b>Studio ready</div>
        <div class="status-pill"><b></b>PDF · DOCX · TXT</div><div class="status-pill"><b></b>Private document processing</div></div>""",
        unsafe_allow_html=True,
    )
    st.markdown(
        """<section class="hero"><div class="eyebrow"><span></span>AI that sounds like you</div>
        <h1>Turn your writing into an <em>unmistakable voice.</em></h1>
        <p>Teach Inkprint how you think, explain, and connect. Then turn any idea into a polished blog post that feels naturally yours.</p></section>""",
        unsafe_allow_html=True,
    )
    writer, library, how = st.tabs(["✦  Writing studio", "▤  Library", "◌  How it works"])
    with writer:
        writer_tab(agent)
    with library:
        library_tab()
    with how:
        about_tab()

    st.markdown(
        "<p style='text-align:center;color:#91a097;font-size:.72rem;margin:2.5rem 0 1rem'>Built with DigitalOcean Gradient AI · Memori · Streamlit</p>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
