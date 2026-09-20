import hashlib

import streamlit as st
import google.generativeai as genai

# ---------- Page Config ----------
st.set_page_config(
    page_title="CMA Trainer Pro",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Styling ----------
st.markdown(
    """
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        border: none;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #4f46e5 0%, #9333ea 100%);
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- API Key Setup ----------
# The secret NAME is GEMINI_API_KEY. The actual key goes in Streamlit Secrets,
# never in this file.
if "GEMINI_API_KEY" not in st.secrets:
    st.error(
        "⚠️ GEMINI_API_KEY missing! Add it in Streamlit Cloud -> Settings -> Secrets:\n\n"
        'GEMINI_API_KEY = "your-key-here"'
    )
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Model name can be changed from Secrets without editing code:
# GEMINI_MODEL = "gemini-2.5-flash"
MODEL_NAME = st.secrets.get("GEMINI_MODEL", "gemini-2.5-flash")
model = genai.GenerativeModel(MODEL_NAME)


def ask_ai(prompt):
    """Call the model and return text, or show a friendly error."""
    try:
        return model.generate_content(prompt).text
    except Exception as e:
        st.error(f"AI error: {e}")
        return None


# ---------- Syllabus Data ----------
cma_syllabus = {
    "Group 1": {
        "Paper 5: Business Laws and Ethics": "Indian Contract Act, Sale of Goods Act, Corporate Governance, Ethics.",
        "Paper 6: Financial Accounting": "GAAP, Partnership Accounting, Non-Profit Organizations, Accounting Standards.",
        "Paper 7: Direct and Indirect Taxation": "Income Tax Act 1961, Computation of Income, GST Registration & Returns, Customs Duty.",
        "Paper 8: Cost Accounting": "Material & Labour Costing, Standard & Marginal Costing, CVP Analysis.",
    },
    "Group 2": {
        "Paper 9: Operations & Strategic Management": "Production Planning, Inventory Management, Business Policy, CSR.",
        "Paper 10: Corporate Accounting and Auditing": "Company Accounts, Auditing Standards, Types of Audits.",
        "Paper 11: Financial Management & Business Data Analytics": "Capital Budgeting, Working Capital, Data Science for Business.",
        "Paper 12: Management Accounting": "Standard Costing, Variance Analysis, Budgetary Control, Decision Theory.",
    },
}

# ---------- Sidebar ----------
st.sidebar.markdown("# 🎓 CMA Trainer Pro")
st.sidebar.markdown("*Your 24/7 Personal ICMAI Mentor*")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navigation",
    [
        "💬 AI Doubt Solver",
        "📖 Quick Revision Guides",
        "📜 Chat History & Logs",
        "📚 Study Notes & CAS",
        "⭐ Saved Important Doubts",
        "📝 MCQ Practice & Test",
        "✍️ Model Exam Evaluator",
    ],
)

# ---------- Session State ----------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "starred_doubts" not in st.session_state:
    st.session_state.starred_doubts = []
if "chat_history_archive" not in st.session_state:
    st.session_state.chat_history_archive = []
if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None

# ---------- 1. AI Doubt Solver ----------
if menu == "💬 AI Doubt Solver":
    st.title("💬 Interactive AI Doubt Solver")
    st.markdown("Ask any concept, numerical problem, or law section doubt based on the ICMAI 2022 Syllabus.")

    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                if st.button("⭐ Save Doubt", key=f"star_{idx}"):
                    if message["content"] not in st.session_state.starred_doubts:
                        st.session_state.starred_doubts.append(message["content"])
                        st.success("Saved to Important Doubts!")

    prompt = st.chat_input("Type your CMA doubt here...")
    audio_file = st.audio_input("🎙️ Or click to record your voice doubt:")

    query_to_process = None
    if prompt:
        query_to_process = prompt
    elif audio_file:
        # Streamlit reruns the script on every click, so only process a
        # recording once (otherwise the same audio gets re-asked each time).
        audio_bytes = audio_file.getvalue()
        audio_hash = hashlib.md5(audio_bytes).hexdigest()
        if audio_hash != st.session_state.last_audio_hash:
            st.session_state.last_audio_hash = audio_hash
            st.info("Processing voice input...")
            try:
                audio_resp = model.generate_content(
                    [
                        {"mime_type": "audio/wav", "data": audio_bytes},
                        "Transcribe this audio query accurately regarding CMA studies. Return only the transcription.",
                    ]
                )
                query_to_process = audio_resp.text
            except Exception as e:
                st.error(f"Audio processing error: {e}")

    if query_to_process:
        st.session_state.messages.append({"role": "user", "content": query_to_process})
        with st.chat_message("user"):
            st.markdown(query_to_process)

        with st.chat_message("assistant"):
            with st.spinner("CMA Trainer analysing concept..."):
                # Include the last few messages so follow-up doubts make sense
                recent = st.session_state.messages[-7:-1]
                context = "\n".join(f"{m['role']}: {m['content']}" for m in recent)
                sys_prompt = (
                    "You are an expert ICMAI Professor. Give a clear, structured, "
                    "professional explanation.\n"
                    f"Earlier conversation (may be empty):\n{context}\n\n"
                    f"Student's question: {query_to_process}"
                )
                ans_text = ask_ai(sys_prompt)
                if ans_text:
                    st.markdown(ans_text)
                    st.session_state.messages.append({"role": "assistant", "content": ans_text})
                    st.session_state.chat_history_archive.append(
                        {"question": query_to_process, "answer": ans_text}
                    )

# ---------- 2. Quick Revision Guides ----------
elif menu == "📖 Quick Revision Guides":
    st.title("📖 ICMAI Exam Revision Guides")
    st.markdown("Instant point-to-point exam summaries, formulas, and last-minute revision checklists.")

    group_choice = st.selectbox("Choose Group for Revision:", ["Group 1", "Group 2"])
    selected_guide_paper = st.selectbox("Choose Paper for Guide:", list(cma_syllabus[group_choice].keys()))

    if st.button("Generate Quick Revision Guide"):
        with st.spinner("Compiling high-yield revision points..."):
            text = ask_ai(
                f"Act as an expert CMA mentor. Create a comprehensive, high-yield, point-to-point "
                f"quick revision guide for {selected_guide_paper} covering key sections, practical "
                f"format formulas, and most important exam points."
            )
            if text:
                st.markdown(text)

# ---------- 3. Chat History & Logs ----------
elif menu == "📜 Chat History & Logs":
    st.title("📜 Past Questions & Chat History")
    if not st.session_state.chat_history_archive:
        st.info("No chat history found yet.")
    else:
        if st.button("🗑️ Clear History Log"):
            st.session_state.chat_history_archive = []
            st.rerun()

        total = len(st.session_state.chat_history_archive)
        for i, hist in enumerate(reversed(st.session_state.chat_history_archive)):
            with st.expander(f"Q{total - i}: {hist['question'][:60]}..."):
                st.markdown(f"**Question:** {hist['question']}")
                st.markdown(f"**Answer:**\n{hist['answer']}")

# ---------- 4. Study Notes & CAS ----------
elif menu == "📚 Study Notes & CAS":
    st.title("📚 Comprehensive Study Notes & CAS Reference")
    group = st.selectbox("Select Group:", ["Group 1", "Group 2"])
    selected_paper = st.selectbox("Select Paper:", list(cma_syllabus[group].keys()))
    st.info(f"**Core Syllabus Coverage:** {cma_syllabus[group][selected_paper]}")

    if st.button("🚀 Generate Detailed Master Notes"):
        with st.spinner("Generating deep-dive professional notes..."):
            text = ask_ai(
                f"Act as a top CMA Professor. Provide structured chapter notes, important "
                f"sections, and exam tips for {selected_paper}."
            )
            if text:
                st.markdown(text)

# ---------- 5. Saved Important Doubts ----------
elif menu == "⭐ Saved Important Doubts":
    st.title("⭐ Your Bookmarked Doubts & Revision Notes")
    if not st.session_state.starred_doubts:
        st.info("No doubts starred yet!")
    else:
        for i, doubt in enumerate(st.session_state.starred_doubts):
            with st.expander(f"Revision Item #{i + 1}"):
                st.markdown(doubt)
                if st.button(f"Delete #{i + 1}", key=f"del_{i}"):
                    st.session_state.starred_doubts.pop(i)
                    st.rerun()

# ---------- 6. MCQ Practice & Test ----------
elif menu == "📝 MCQ Practice & Test":
    st.title("📝 Interactive MCQ Practice Engine")
    all_papers = list(cma_syllabus["Group 1"].keys()) + list(cma_syllabus["Group 2"].keys())
    sub = st.selectbox("Choose Subject for Quiz:", all_papers)

    if st.button("Generate 5 Practice MCQs"):
        with st.spinner("Creating exam-standard questions..."):
            text = ask_ai(
                f"Create 5 multiple choice questions with options (A, B, C, D) and answers "
                f"at the end for CMA exam on: {sub}"
            )
            if text:
                st.markdown(text)

# ---------- 7. Model Exam Evaluator ----------
elif menu == "✍️ Model Exam Evaluator":
    st.title("✍️ AI Descriptive Answer Evaluator")
    exam_q = st.text_input("Enter Exam Question / Case Study:")
    student_ans = st.text_area("Your Written Answer:")

    if st.button("Evaluate Answer"):
        if exam_q and student_ans:
            with st.spinner("Evaluating according to ICMAI guidelines..."):
                text = ask_ai(
                    f"Evaluate this CMA exam answer strictly. Question: {exam_q} | "
                    f"Student Answer: {student_ans}. Provide Marks out of 10, detailed critique, "
                    f"and ideal answer guidelines."
                )
                if text:
                    st.markdown(text)
        else:
            st.warning("Please fill both question and your answer.")
