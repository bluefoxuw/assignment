import streamlit as st
import pdfplumber
import re
from openai import OpenAI
import os
from dotenv import load_dotenv
from time import sleep

# Load .env if local
load_dotenv()

# Secret from Render environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Extract questions from uploaded PDF
def extract_questions_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text(keep_blank_chars=False) + "\n"

    clean_text = re.sub(
        r'(P\.T\.O\.|\[6173\]-\d+|{3}|SEAT No\. :).*?(\n\s*Q\d+\)|$)',
        r'\2',
        text,
        flags=re.DOTALL
    )
    clean_text = re.sub(r'\s*\[\d+\]', '', clean_text)

    questions = re.findall(
        r'(Q\d+\)(?:[^\nQ]|\n(?!Q\d+\)|\s*$))*)',
        clean_text
    )

    return [q.strip() for q in questions if q.strip()]

# Get answer from OpenAI
def get_answer(question):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a computer Science professor. Answer concisely with examples where needed."},
                {"role": "user", "content": f"Answer this exam question:\n\n{question}"}
            ],
            max_tokens=200,
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# Streamlit UI
st.title("📄 PDF Question Paper Answer Bot")

uploaded_file = st.file_uploader("Upload a PDF question paper", type=["pdf"])

if uploaded_file:
    st.info("⏳ Extracting questions from PDF...")
    questions = extract_questions_from_pdf(uploaded_file)
    st.success(f"✅ Found {len(questions)} questions.")

    if st.button("Get Answers"):
        for i, question in enumerate(questions[:5]):  # Limit for safety
            st.markdown(f"###{question}")
            with st.spinner("Getting answer..."):
                answer = get_answer(question)
            st.markdown(f"**Answer:** {answer}")
            sleep(2)  # avoid hitting rate limits
