import os
import base64
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from datetime import datetime

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


# ---------------------------
# Core functions
# ---------------------------

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.read()).decode("utf-8")


def analyze_single_image(base64_image, mime_type, prompt):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}
                    }
                ]
            }
        ]
    )
    return response.choices[0].message.content


def chat_with_image(conversation_history):
    response = client.chat.completions.create(
        model=MODEL,
        messages=conversation_history
    )
    return response.choices[0].message.content


OCR_PROMPT = (
    "Extract all text visible in this image exactly as it appears. "
    "Preserve formatting where possible. If there's no readable text, say 'No text found.'"
)

DESCRIBE_PROMPT = "Describe this image in detail."


# ---------------------------
# Page setup + styling
# ---------------------------

st.set_page_config(page_title="AI Image Analyzer", page_icon="🖼️", layout="centered")

st.markdown("""
<style>
    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.2rem;
        background: linear-gradient(90deg, #6366f1, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .subtitle {
        text-align: center;
        color: #9ca3af;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    .stButton>button {
        background: linear-gradient(90deg, #6366f1, #ec4899);
        color: white;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        width: 100%;
    }
    .result-box {
        background-color: #1e1e2e;
        border: 1px solid #3f3f5a;
        border-radius: 12px;
        padding: 1.2rem;
        margin-top: 0.8rem;
        margin-bottom: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🖼️ AI Image Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload one or more images — chat, extract text, or batch analyze</div>', unsafe_allow_html=True)


# ---------------------------
# Session state setup
# ---------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_file_id" not in st.session_state:
    st.session_state.current_file_id = None
if "batch_results" not in st.session_state:
    st.session_state.batch_results = []


# ---------------------------
# Mode selector
# ---------------------------

app_mode = st.radio(
    "Mode",
    ["💬 Chat about an image", "📝 Extract text (OCR)", "📦 Batch analyze multiple images"],
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()


# ---------------------------
# MODE 1: Chat about a single image
# ---------------------------

if app_mode == "💬 Chat about an image":
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"], key="chat_upload")

    if uploaded_file is not None:
        file_id = uploaded_file.name + str(uploaded_file.size)

        # Reset conversation if a different image was uploaded
        if st.session_state.current_file_id != file_id:
            base64_image = encode_image(uploaded_file)
            st.session_state.base64_image = base64_image
            st.session_state.mime_type = uploaded_file.type
            st.session_state.current_file_id = file_id
            st.session_state.messages = []

        st.image(uploaded_file, caption="Uploaded image", use_column_width=True)

        for msg in st.session_state.messages:
            if msg["role"] == "user":
                if isinstance(msg["content"], list):
                    text_part = next((c["text"] for c in msg["content"] if c.get("type") == "text"), "")
                else:
                    text_part = msg["content"]
                st.chat_message("user").write(text_part)
            else:
                st.chat_message("assistant").write(msg["content"])

        user_question = st.chat_input("Ask something about the image...")

        if user_question:
            if len(st.session_state.messages) == 0:
                st.session_state.messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_question},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{st.session_state.mime_type};base64,{st.session_state.base64_image}"}
                        }
                    ]
                })
            else:
                st.session_state.messages.append({"role": "user", "content": user_question})

            st.chat_message("user").write(user_question)

            with st.spinner("Thinking..."):
                reply = chat_with_image(st.session_state.messages)

            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.chat_message("assistant").write(reply)

        # Export conversation as markdown
        if st.session_state.messages:
            md_lines = [f"# Image Analysis Chat\n", f"_Exported {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n"]
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    text_part = msg["content"][0]["text"] if isinstance(msg["content"], list) else msg["content"]
                    md_lines.append(f"**You:** {text_part}\n")
                else:
                    md_lines.append(f"**AI:** {msg['content']}\n")
            md_content = "\n".join(md_lines)

            st.download_button(
                "⬇️ Download conversation as Markdown",
                data=md_content,
                file_name="image_chat.md",
                mime="text/markdown"
            )
    else:
        st.session_state.current_file_id = None
        st.info("👆 Upload an image to start chatting about it")


# ---------------------------
# MODE 2: OCR
# ---------------------------

elif app_mode == "📝 Extract text (OCR)":
    uploaded_file = st.file_uploader("Upload an image with text", type=["jpg", "jpeg", "png"], key="ocr_upload")

    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded image", use_column_width=True)

        if st.button("📝 Extract Text"):
            base64_image = encode_image(uploaded_file)
            mime_type = uploaded_file.type

            with st.spinner("Reading text from image..."):
                extracted_text = analyze_single_image(base64_image, mime_type, OCR_PROMPT)

            st.markdown(f'<div class="result-box">{extracted_text}</div>', unsafe_allow_html=True)

            st.download_button(
                "⬇️ Download extracted text",
                data=extracted_text,
                file_name="extracted_text.md",
                mime="text/markdown"
            )
    else:
        st.info("👆 Upload an image containing text (screenshot, document, sign, etc.)")


# ---------------------------
# MODE 3: Batch analyze
# ---------------------------

elif app_mode == "📦 Batch analyze multiple images":
    uploaded_files = st.file_uploader(
        "Upload multiple images",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key="batch_upload"
    )

    custom_prompt = st.text_input(
        "What should the AI tell you about each image?",
        value="Describe this image in detail."
    )

    if uploaded_files:
        st.write(f"**{len(uploaded_files)} image(s) ready to analyze**")

        if st.button("🚀 Analyze All"):
            st.session_state.batch_results = []
            progress_bar = st.progress(0, text="Starting batch analysis...")

            total = len(uploaded_files)
            for i, file in enumerate(uploaded_files):
                progress_bar.progress(
                    (i) / total,
                    text=f"Analyzing image {i + 1} of {total}: {file.name}"
                )

                base64_image = encode_image(file)
                mime_type = file.type
                result = analyze_single_image(base64_image, mime_type, custom_prompt)

                st.session_state.batch_results.append({
                    "filename": file.name,
                    "result": result
                })

            progress_bar.progress(1.0, text="Done!")

        if st.session_state.batch_results:
            st.divider()
            st.subheader("Results")

            md_lines = [f"# Batch Image Analysis\n", f"_Exported {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n"]

            for item in st.session_state.batch_results:
                with st.expander(f"📄 {item['filename']}"):
                    st.write(item["result"])
                md_lines.append(f"## {item['filename']}\n\n{item['result']}\n")

            md_content = "\n".join(md_lines)

            st.download_button(
                "⬇️ Download all results as Markdown",
                data=md_content,
                file_name="batch_analysis.md",
                mime="text/markdown"
            )
    else:
        st.info("👆 Upload multiple images to analyze them all at once")