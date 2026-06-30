---
title: AI Image Analyzer
emoji: 🖼️
colorFrom: indigo
colorTo: pink
sdk: streamlit
sdk_version: "1.38.0"
app_file: main.py
pinned: false
---

# 🖼️ AI Image Analyzer

An AI-powered tool for analyzing, chatting about, and extracting text from images.

## Features
- **Chat about an image** — upload an image and ask follow-up questions in a conversational interface
- **OCR (text extraction)** — pull readable text out of any image (screenshots, documents, signs)
- **Batch analysis** — upload multiple images at once, apply one prompt to all, with live progress tracking
- **Export results** — download conversations or batch results as Markdown

## Tech Stack
- **Python**
- **Streamlit** — web interface
- **Groq API** — vision-language model (Llama 4 Scout)

## Setup
1. Clone this repo
2. Install dependencies: `pip install streamlit groq python-dotenv`
3. Create a `.env` file with your Groq API key:
4. Run: `streamlit run main.py`

---
Built as a learning project to explore multimodal AI and image-based automation.