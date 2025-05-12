import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import os
import urllib.request

from dotenv import load_dotenv
import os

# load_dotenv(dotenv_path="/workspaces/Beginner-Investment-Advisor-Introduction-to-Programming/.env")
load_dotenv()

print("KEY LOADED:", os.getenv("OPENAI_API_KEY"))



from openai import OpenAI
client=OpenAI(
  base_url="https://openrouter.ai/api/v1"
)
    
from MertCodev1 import (
    QUESTIONNAIRE,
    map_answers_to_profile,
    derive_risk_level,
    get_region_risk_etf,
    generate_full_recommendation,
    PRODUCT_INFO,   
    tick_labels,
    RISK_LEVEL_NAME
)

from fpdf import FPDF

def clean_text_for_pdf(text):
    text = text.replace("–", "-").replace("—", "-")
    return text.encode("ascii", "ignore").decode()

# ✅ Email Configuration (Step 1)
EMAIL_SENDER = "Investmentguideprogramming@gmx.de"
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = "mail.gmx.net"
SMTP_PORT = 587

import smtplib
from email.message import EmailMessage

#Email Configuration (Step 2)
def send_email_with_pdf(receiver_email, pdf_filename):
    msg = EmailMessage()
    msg["Subject"] = "Your Investment Report"
    msg["From"] = EMAIL_SENDER
    msg["To"] = receiver_email
    msg.set_content("Hi! Please find attached your personal investment report.")

    with open(pdf_filename, "rb") as f:
        file_data = f.read()
        file_name = f.name
    msg.add_attachment(file_data, maintype="application", subtype="pdf", filename=file_name)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)


# PDF Generation
def generate_pdf_report(profile, recommendations, explanation_text, filename="investment_report.pdf"):
    pdf = FPDF()
    pdf.add_page()

    # 👉 Font hinzufügen (wichtig: richtige Pfadangabe!)
    pdf.add_font("DejaVu", "", "Fonts/DejaVuSans.ttf", uni=True)
    pdf.set_font("DejaVu", size=12)

    pdf.cell(200, 10, txt="Investment Report", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("DejaVu", size=11)
    pdf.multi_cell(0, 10, f"Risk Level: {profile.get('risk_level', 'Unknown')} ({RISK_LEVEL_NAME.get(profile.get('risk_level'), '')})")
    pdf.ln(5)

    pdf.set_font("DejaVu", size=10)
    pdf.multi_cell(0, 10, explanation_text)
    pdf.ln(5)

    pdf.set_font("DejaVu", size=11)
    pdf.cell(0, 10, "Recommendations:", ln=True)
    pdf.ln(3)

    for rec in recommendations:
        line = f"{rec['ticker']} - {rec['region']} ({rec['asset_class']}), Score: {rec.get('final_score', 0):.2f}, ESG: {rec.get('esgScore', 'N/A')}"
        pdf.multi_cell(0, 10, clean_text_for_pdf(line))
        pdf.ln(1)

    pdf.output(filename)
    return filename

#Chat gpt
def explain_recommendations_with_gpt(profile, recommendations, name):
    risk_level = profile.get("risk_level", "Unknown")
    risk_label = RISK_LEVEL_NAME.get(risk_level, "No label")

    def format_recs(recs):
        return "\n".join(
            f"- {r['ticker']} ({r['region']}, {r['asset_class']}), ESG: {r.get('esgScore', 'N/A')}, Score: {r.get('final_score', 0):.2f}"
            for r in recs[:5]
        )

    prompt = f"""
You are a friendly financial advisor helping a beginner named {name}.
Write a clear and simple explanation for the following investment profile:

Risk Level: {risk_level} – {risk_label}

ETF Recommendations:
{format_recs(recommendations)}

Instructions:
- Start with a personal greeting to {name}
- Briefly explain what the risk level means
- Describe why these ETFs are suitable
- Use simple, beginner-friendly language
- End with an encouraging statement
"""

    response = client.chat.completions.create(
        model="deepseek/deepseek-prover-v2:free",  # or gpt-4o-mini
        messages=[
            {"role": "system", "content": "You are a helpful and friendly financial assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

# beginning of the Streamlit app
st.set_page_config(page_title="Beginner Investment Advisor", layout="wide")

# Name input at the beginning
if "name" not in st.session_state:
    st.session_state.name = ""
if "current_question" not in st.session_state:
    st.session_state.current_question = 0
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "questionnaire_complete" not in st.session_state:
    st.session_state.questionnaire_complete = False

if not st.session_state.name:
    st.title("Welcome to the Beginner Investment Advisor")
    with st.form(key="name_form", clear_on_submit=True):
        name_input = st.text_input("Please enter your name to begin:")
        email_input = st.text_input("And your email address:")
        start_clicked = st.form_submit_button("Start")
        if start_clicked and name_input.strip() and email_input.strip():
            st.session_state.name = name_input.strip()
            st.session_state.email = email_input.strip()
            st.rerun()
elif not st.session_state.questionnaire_complete:
    st.title(f"Welcome, {st.session_state.name}!")
    current_question_index = st.session_state.current_question
    question = QUESTIONNAIRE[current_question_index]
    with st.form(key=f"question_form_{current_question_index}", clear_on_submit=True):
        st.markdown(f"""
    <div style='padding: 1.5em 0 1em 0;'>
        <span style='font-size:1.5em; font-weight:bold; color:#1a237e;'>Question {current_question_index + 1} of {len(QUESTIONNAIRE)}</span><br>
        <span style='font-size:1.2em; font-weight:bold; color:#222;'>{question['text']}</span>
    </div>
""", unsafe_allow_html=True)
        answer = st.radio(
            "",
            question["options"],
            key=f"q_{current_question_index}_radio",
            index=st.session_state.answers.get(current_question_index, 0)
        )
        col1, col2 = st.columns([1,1])
        with col1:
            back_clicked = st.form_submit_button("Back") if current_question_index > 0 else False
        with col2:
            next_clicked = st.form_submit_button("Next")
        if back_clicked:
            st.session_state.current_question -= 1
            st.rerun()
        elif next_clicked:
            st.session_state.answers[current_question_index] = question["options"].index(answer)
            if current_question_index + 1 < len(QUESTIONNAIRE):
                st.session_state.current_question += 1
                st.rerun()
            else:
                st.session_state.questionnaire_complete = True
                st.rerun()
else:
    answers = st.session_state.answers
    profile = map_answers_to_profile(answers)
    rl = derive_risk_level(answers)
    st.title(f"Thank you, {st.session_state.name}!")
    st.write("✅ You have completed the questionnaire!")
    st.markdown("⏳ Please be patient while we prepare your personalized results – maybe grab a popcorn 🍿 while we crunch the numbers!")
    
# Show quick summary
profile = map_answers_to_profile(st.session_state.answers)
risk_level = derive_risk_level(st.session_state.answers)
region = "Europe"  # or allow user to choose region earlier in your app
result = generate_full_recommendation(st.session_state.answers)

primary = result["primary_etf"]
recommendations = result["recommendations"]

st.subheader("📊 Your Investment Summary")
st.markdown(f"""
**Risk Level:** {risk_level} – *{RISK_LEVEL_NAME[risk_level]}*  
**Primary ETF Recommendation:** `{primary['ticker']}`  
""")

from collections import defaultdict

grouped = defaultdict(list)
for r in recommendations:
    grouped[r["region"]].append(r)

for region in ["Europe", "North America", "Emerging Markets"]:
    st.subheader(f"🌍 {region}")
    for r in grouped.get(region, []):
        name, asset_type = PRODUCT_INFO.get(r["ticker"], ("Unknown", r["asset_class"]))
        st.markdown(
            f"- **{name}** ({asset_type}) – ESG: {r.get('esgScore', 'N/A')}, "
            f"Score: {r.get('final_score', 0):.2f}"
        )

gpt_text = explain_recommendations_with_gpt(profile, recommendations, st.session_state.name)
st.subheader("Your Personalized Investment Explanation")
st.write(gpt_text)

if st.button("Get Detailed Report by Email"):
   filename = generate_pdf_report(profile, recommendations, gpt_text, st.session_state.name)
   send_email_with_pdf(st.session_state.email, filename)
   st.success("Report sent to your email!")