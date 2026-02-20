import streamlit as st
import time

# ─── Page config ───
st.set_page_config(
    page_title="RAG AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Theme-aware CSS ───
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── Base ── */
html, body, .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
#MainMenu, footer, .stDeployButton { display: none !important; }
header[data-testid="stHeader"] { background: transparent !important; }

/* ── Soft background ── */
.stApp {
    background-color: #131320 !important;
    background-image:
        radial-gradient(ellipse 80% 60% at 15% 30%, rgba(99, 102, 241, 0.06), transparent),
        radial-gradient(ellipse 60% 50% at 85% 70%, rgba(168, 85, 247, 0.045), transparent);
}

/* ══════════════════════════════════════════
   SIDEBAR
   ══════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d0d15 0%, #111119 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.03) !important;
}

/* Sidebar text colors */
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #9ca3af !important;
    font-size: 0.95rem;
}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
    color: #e5e7eb !important;
}

/* Sidebar buttons */
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    color: #9ca3af !important;
    border-radius: 10px !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(99, 102, 241, 0.08) !important;
    border-color: rgba(99, 102, 241, 0.2) !important;
    color: #c4b5fd !important;
}

/* ══════════════════════════════════════════
   CHAT MESSAGE STYLING
   ══════════════════════════════════════════ */

/* User messages */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.12), rgba(139, 92, 246, 0.08)) !important;
    border: 1px solid rgba(99, 102, 241, 0.15) !important;
    border-radius: 16px !important;
    padding: 1rem 1.2rem !important;
    margin-bottom: 0.5rem !important;
}

/* AI messages */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background: rgba(255, 255, 255, 0.02) !important;
    border: 1px solid rgba(255, 255, 255, 0.04) !important;
    border-radius: 16px !important;
    padding: 1rem 1.2rem !important;
    margin-bottom: 0.5rem !important;
}

/* Chat message text */
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
    color: #d1d5db !important;
    font-size: 1rem !important;
    line-height: 1.7 !important;
}

/* User avatar */
[data-testid="chatAvatarIcon-user"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
}

/* Assistant avatar */
[data-testid="chatAvatarIcon-assistant"] {
    background: linear-gradient(135deg, #8b5cf6, #a855f7) !important;
}

/* ══════════════════════════════════════════
   CHAT INPUT — Enhanced floating bar
   ══════════════════════════════════════════ */
[data-testid="stChatInput"] {
    padding: 0.8rem 1rem 1.2rem 1rem !important;
    border-top: none !important;
    position: relative;
}
[data-testid="stChatInput"]::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 40px;
    background: linear-gradient(to top, #0b0b0f, transparent);
    pointer-events: none;
    z-index: 0;
}
[data-testid="stChatInput"] > div {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 16px !important;
    transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 2px 20px rgba(0,0,0,0.3), 0 0 0 0 rgba(99,102,241,0) !important;
    backdrop-filter: blur(12px) !important;
    padding: 4px !important;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: rgba(99, 102, 241, 0.35) !important;
    box-shadow:
        0 2px 25px rgba(0,0,0,0.4),
        0 0 0 3px rgba(99, 102, 241, 0.06),
        0 0 40px rgba(99, 102, 241, 0.06) !important;
    background: rgba(255,255,255,0.04) !important;
}
[data-testid="stChatInput"] textarea {
    color: #e5e7eb !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1rem !important;
    padding: 0.6rem 0.8rem !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #4b5563 !important;
}
[data-testid="stChatInput"] button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    border: none !important;
    border-radius: 12px !important;
    width: 38px !important;
    height: 38px !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 2px 10px rgba(99,102,241,0.2) !important;
}
[data-testid="stChatInput"] button:hover {
    transform: scale(1.05) !important;
    box-shadow: 0 4px 20px rgba(99, 102, 241, 0.35) !important;
}
[data-testid="stChatInput"] button:active {
    transform: scale(0.95) !important;
}

/* ══════════════════════════════════════════
   CUSTOM COMPONENTS
   ══════════════════════════════════════════ */

/* Hero */
.hero-section {
    text-align: center;
    padding: 2rem 1rem 0.5rem 1rem;
    max-width: 700px;
    margin: 0 auto;
}
.hero-label {
    display: inline-block;
    background: rgba(99, 102, 241, 0.08);
    border: 1px solid rgba(99, 102, 241, 0.15);
    padding: 5px 16px;
    border-radius: 100px;
    font-size: 0.72rem;
    font-weight: 600;
    color: #a5b4fc;
    letter-spacing: 0.5px;
    margin-bottom: 1.2rem;
}
.hero-heading {
    font-size: 2.8rem;
    font-weight: 800;
    letter-spacing: -1.5px;
    line-height: 1.1;
    margin: 0 0 0.8rem 0;
    color: #f3f4f6;
}
.hero-heading .gradient {
    background: linear-gradient(135deg, #818cf8, #a78bfa, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero-desc {
    font-size: 1rem;
    color: #6b7280;
    font-weight: 350;
    line-height: 1.65;
    margin: 0 auto;
    max-width: 480px;
}

/* Feature pills */
.features-row {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 8px;
    margin: 2rem auto 1.5rem auto;
    max-width: 650px;
}
.feature-pill {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.05);
    padding: 8px 16px;
    border-radius: 100px;
    font-size: 0.78rem;
    color: #9ca3af;
    font-weight: 450;
    transition: all 0.25s ease;
    cursor: default;
}
.feature-pill:hover {
    border-color: rgba(99, 102, 241, 0.25);
    background: rgba(99, 102, 241, 0.05);
    color: #c4b5fd;
    transform: translateY(-1px);
}
.pill-icon {
    font-size: 0.85rem;
}

/* Prompt starters */
.starters {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 8px;
    margin: 2rem auto;
    max-width: 700px;
}
.starter-btn {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.05);
    padding: 10px 18px;
    border-radius: 12px;
    font-size: 0.82rem;
    color: #6b7280;
    font-family: 'Inter', sans-serif;
    transition: all 0.2s ease;
    cursor: pointer;
    text-align: left;
    line-height: 1.4;
}
.starter-btn:hover {
    border-color: rgba(99, 102, 241, 0.2);
    background: rgba(99, 102, 241, 0.04);
    color: #a5b4fc;
    transform: translateY(-1px);
}
.starter-icon {
    margin-right: 6px;
    opacity: 0.5;
}

/* Thin separator */
.sep {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.04), transparent);
    margin: 0.5rem 0;
}

/* Status badge */
.live-badge {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: rgba(16, 185, 129, 0.06);
    border: 1px solid rgba(16, 185, 129, 0.12);
    padding: 6px 14px;
    border-radius: 100px;
    font-size: 0.72rem;
    color: #34d399;
    font-weight: 500;
}
.live-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #10b981;
    box-shadow: 0 0 6px rgba(16,185,129,0.4);
    animation: blink 2s ease-in-out infinite;
}
@keyframes blink {
    0%, 100% { opacity: 0.4; }
    50% { opacity: 1; }
}

/* Sidebar section headers */
.sb-label {
    font-size: 0.62rem;
    font-weight: 700;
    color: #4b5563;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin: 1rem 0 0.6rem 0;
}

/* Sidebar stat row */
.sb-stats {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin: 0.5rem 0;
}
.sb-stat {
    background: rgba(255,255,255,0.015);
    border: 1px solid rgba(255,255,255,0.03);
    border-radius: 10px;
    padding: 14px 10px;
    text-align: center;
    transition: all 0.2s ease;
}
.sb-stat:hover {
    border-color: rgba(99, 102, 241, 0.15);
    transform: translateY(-1px);
}
.sb-stat-num {
    font-size: 1.5rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    background: linear-gradient(135deg, #818cf8, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1;
}
.sb-stat-lbl {
    font-size: 0.58rem;
    font-weight: 700;
    color: #4b5563;
    text-transform: uppercase;
    letter-spacing: 1.3px;
    margin-top: 5px;
}

/* Info row (key-value) */
.info-grid {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin: 0.5rem 0;
}
.info-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    border-radius: 8px;
    background: rgba(255,255,255,0.012);
    transition: background 0.15s;
}
.info-row:hover { background: rgba(255,255,255,0.025); }
.info-key {
    font-size: 0.78rem;
    color: #9ca3af;
    display: flex;
    align-items: center;
    gap: 7px;
}
.info-val {
    font-size: 0.72rem;
    font-family: 'JetBrains Mono', monospace;
    color: #818cf8;
    font-weight: 500;
    background: rgba(99, 102, 241, 0.06);
    padding: 2px 8px;
    border-radius: 5px;
}

/* Tech badge */
.tech-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    margin: 0.5rem 0;
}
.tech-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.04);
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.65rem;
    color: #6b7280;
    font-weight: 500;
    transition: all 0.2s;
}
.tech-badge:hover {
    border-color: rgba(99, 102, 241, 0.15);
    color: #a5b4fc;
}
.tech-badge-icon { font-size: 0.7rem; }

/* Pipeline step */
.pipe-step {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 7px 10px;
    border-radius: 8px;
    font-size: 0.85rem;
    color: #9ca3af;
    transition: background 0.15s;
}
.pipe-step:hover { background: rgba(255,255,255,0.02); }
.pipe-num {
    width: 22px; height: 22px;
    border-radius: 7px;
    background: rgba(99, 102, 241, 0.1);
    color: #818cf8;
    font-size: 0.65rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.pipe-text { flex: 1; color: #d1d5db; }
.pipe-tag {
    font-size: 0.58rem;
    font-family: 'JetBrains Mono', monospace;
    color: #4b5563;
    background: rgba(255,255,255,0.02);
    padding: 2px 7px;
    border-radius: 4px;
}

/* Sidebar divider */
.sb-div {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.04), transparent);
    margin: 0.8rem 0;
}

/* Sidebar footer hint */
.sb-hint {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    border-radius: 8px;
    background: rgba(99, 102, 241, 0.04);
    border: 1px solid rgba(99, 102, 241, 0.08);
    margin-top: 0.5rem;
}
.sb-hint-icon {
    font-size: 0.85rem;
    opacity: 0.6;
}
.sb-hint-text {
    font-size: 0.7rem;
    color: #6b7280;
    line-height: 1.4;
}
.sb-hint-text span {
    color: #818cf8;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    background: rgba(99,102,241,0.08);
    padding: 1px 5px;
    border-radius: 3px;
}

/* Source tag displayed under AI message */
.src-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    margin-top: 4px;
}
.src-tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(99, 102, 241, 0.06);
    border: 1px solid rgba(99, 102, 241, 0.1);
    padding: 3px 10px;
    border-radius: 100px;
    font-size: 0.65rem;
    color: #818cf8;
    font-weight: 500;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.12); border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

# ─── Session State ───
if "messages" not in st.session_state:
    st.session_state.messages = []
if "total_queries" not in st.session_state:
    st.session_state.total_queries = 0

# ─── Sidebar ───
with st.sidebar:
    # Logo
    st.markdown("""
    <div style="display:flex; align-items:center; gap:10px; padding-bottom:1.2rem; border-bottom:1px solid rgba(255,255,255,0.03); margin-bottom:1rem;">
        <div style="width:34px; height:34px; border-radius:9px; background:linear-gradient(135deg,#6366f1,#8b5cf6); display:flex; align-items:center; justify-content:center; font-size:1rem; box-shadow:0 3px 12px rgba(99,102,241,0.3);">⚡</div>
        <div>
            <div style="font-size:1.2rem; font-weight:700; color:#e5e7eb; letter-spacing:-0.3px;">RAG AI</div>
            <div style="font-size:0.6rem; color:#4b5563; font-weight:600; letter-spacing:1px; text-transform:uppercase;">Document Intelligence</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Status
    st.markdown("""
    <div class="live-badge">
        <span class="live-dot"></span>
        System Online
    </div>
    """, unsafe_allow_html=True)

    # Session stats
    st.markdown('<div class="sb-label">Session</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="sb-stats">
        <div class="sb-stat">
            <div class="sb-stat-num">{st.session_state.total_queries}</div>
            <div class="sb-stat-lbl">Queries</div>
        </div>
        <div class="sb-stat">
            <div class="sb-stat-num">{len(st.session_state.messages) // 2}</div>
            <div class="sb-stat-lbl">Answers</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-div"></div>', unsafe_allow_html=True)

    # System info
    st.markdown('<div class="sb-label">System Info</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-grid">
        <div class="info-row">
            <span class="info-key">🗄️ Vector Chunks</span>
            <span class="info-val">47</span>
        </div>
        <div class="info-row">
            <span class="info-key">📄 Indexed Files</span>
            <span class="info-val">1</span>
        </div>
        <div class="info-row">
            <span class="info-key">🧬 Embedding</span>
            <span class="info-val">Gemini</span>
        </div>
        <div class="info-row">
            <span class="info-key">🔍 Search</span>
            <span class="info-val">Hybrid</span>
        </div>
        <div class="info-row">
            <span class="info-key">🤖 LLM</span>
            <span class="info-val">Gemini Pro</span>
        </div>
        <div class="info-row">
            <span class="info-key">🎯 Reranker</span>
            <span class="info-val">Cohere v3</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-div"></div>', unsafe_allow_html=True)

    # Pipeline
    st.markdown('<div class="sb-label">Retrieval Pipeline</div>', unsafe_allow_html=True)
    steps = [
        ("1", "Query Expansion", "LLM"),
        ("2", "Hybrid Search", "Vec+BM25"),
        ("3", "Rank Fusion", "RRF"),
        ("4", "Reranking", "Cohere"),
        ("5", "Generation", "Gemini"),
    ]
    html = ""
    for num, label, tag in steps:
        html += f"""
        <div class="pipe-step">
            <span class="pipe-num">{num}</span>
            <span class="pipe-text">{label}</span>
            <span class="pipe-tag">{tag}</span>
        </div>"""
    st.markdown(html, unsafe_allow_html=True)

    st.markdown('<div class="sb-div"></div>', unsafe_allow_html=True)

    # Tech stack badges
    st.markdown('<div class="sb-label">Tech Stack</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="tech-badges">
        <span class="tech-badge"><span class="tech-badge-icon">🐍</span> Python</span>
        <span class="tech-badge"><span class="tech-badge-icon">🦜</span> LangChain</span>
        <span class="tech-badge"><span class="tech-badge-icon">🔮</span> ChromaDB</span>
        <span class="tech-badge"><span class="tech-badge-icon">📊</span> BM25</span>
        <span class="tech-badge"><span class="tech-badge-icon">✨</span> Gemini</span>
        <span class="tech-badge"><span class="tech-badge-icon">🎯</span> Cohere</span>
        <span class="tech-badge"><span class="tech-badge-icon">⚡</span> Groq</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-div"></div>', unsafe_allow_html=True)

    # Clear
    if st.button("🗑  Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.total_queries = 0
        st.rerun()

    # Hint at bottom
    st.markdown("""
    <div class="sb-hint">
        <span class="sb-hint-icon">💡</span>
        <span class="sb-hint-text">Type a question below and press <span>Enter</span> or click send</span>
    </div>
    """, unsafe_allow_html=True)


# ─── Main Area ───

# Hero (only when empty)
if not st.session_state.messages:
    st.markdown("""
    <div class="hero-section">
        <div class="hero-label">⚡ Powered by Hybrid Search + Gemini</div>
        <div class="hero-heading">
            Ask your documents<br><span class="gradient">anything.</span>
        </div>
        <div class="hero-desc">
            Advanced RAG with multi-query expansion, hybrid retrieval,
            reciprocal rank fusion, and neural reranking.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Feature pills
    st.markdown("""
    <div class="features-row">
        <div class="feature-pill"><span class="pill-icon">🔍</span> Hybrid Search</div>
        <div class="feature-pill"><span class="pill-icon">📊</span> RRF Fusion</div>
        <div class="feature-pill"><span class="pill-icon">🎯</span> Neural Reranking</div>
        <div class="feature-pill"><span class="pill-icon">🧠</span> Multi-Query</div>
        <div class="feature-pill"><span class="pill-icon">📄</span> Multimodal</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sep"></div>', unsafe_allow_html=True)

    # Prompt suggestions
    st.markdown("""
    <div class="starters">
        <div class="starter-btn"><span class="starter-icon">💡</span> What is self-attention and why is it important?</div>
        <div class="starter-btn"><span class="starter-icon">🔬</span> Explain the transformer architecture</div>
        <div class="starter-btn"><span class="starter-icon">📐</span> How does multi-head attention work?</div>
        <div class="starter-btn"><span class="starter-icon">⚖️</span> Compare encoder and decoder components</div>
    </div>
    """, unsafe_allow_html=True)

# ─── Chat Messages (using Streamlit native) ───
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            st.markdown(msg["sources"], unsafe_allow_html=True)


# ─── Chat Input ───
if prompt := st.chat_input("Ask a question about your documents..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.total_queries += 1

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI response (mock for UI demo)
    with st.chat_message("assistant"):
        # Streaming effect
        placeholder = st.empty()
        mock_answer = (
            "Based on the retrieved documents, here's what I found:\n\n"
            "**Self-attention**, sometimes called intra-attention, is a mechanism "
            "relating different positions of a single sequence to compute a "
            "representation of the sequence. It allows every position in the "
            "encoder to attend to all positions in the previous layer.\n\n"
            "The **Transformer** uses multi-head attention in three different ways:\n"
            "- In encoder-decoder attention layers, queries come from the previous "
            "decoder layer and keys/values come from the encoder output\n"
            "- The encoder contains self-attention layers where all keys, values, "
            "and queries come from the same place\n"
            "- Similarly, self-attention layers in the decoder allow each position "
            "to attend to all positions up to and including that position\n\n"
            "*Source: Attention Is All You Need (Vaswani et al., 2017)*"
        )

        streamed = ""
        for char in mock_answer:
            streamed += char
            placeholder.markdown(streamed + "▌")
            time.sleep(0.008)
        placeholder.markdown(streamed)

        # Source tags
        src_html = """
        <div class="src-tags">
            <span class="src-tag">📄 attention-is-all-you-need.pdf</span>
            <span class="src-tag">📑 Pages 3–5</span>
            <span class="src-tag">🎯 Score: 0.924</span>
        </div>
        """
        st.markdown(src_html, unsafe_allow_html=True)

    st.session_state.messages.append({
        "role": "assistant",
        "content": mock_answer,
        "sources": src_html
    })
    st.rerun()