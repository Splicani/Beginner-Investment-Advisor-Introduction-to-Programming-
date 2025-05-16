
import streamlit as st
import re
import pandas as pd
import urllib.request
from dotenv import load_dotenv
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
from collections import defaultdict
from fpdf import FPDF

# Load environment variables
load_dotenv()

# Configure OpenAI client
from openai import OpenAI
client = OpenAI(base_url="https://openrouter.ai/api/v1")

# Import the backend functions
from MertCodev1 import (
    QUESTIONNAIRE,
    map_answers_to_profile,
    generate_full_recommendation,
    PRODUCT_INFO,   
    tick_labels,
    RISK_LEVEL_NAME,
    ESG_BASE_SCORES
)

# =========================================================================
# 1. HELPER FUNCTIONS
# =========================================================================

def clean_text_for_display(text):
    """Clean text for display in UI or PDF by removing all markdown and special characters"""
    # First remove any "plaintext" prefix/markers that might appear
    text = re.sub(r'`?plaintext`?\.?\s*', '', text)

    # Remove any number of backticks
    text = re.sub(r'`+', '', text)  
    
    # Remove markdown formatting
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*(.+?)\*', r'\1', text)      # Italic
    text = re.sub(r'`(.+?)`', r'\1', text)        # Code
    text = re.sub(r'```[a-z]*\n(.+?)```', r'\1', text, flags=re.DOTALL)  # Code blocks
    text = re.sub(r'#{1,6}\s+(.+)', r'\1', text, flags=re.MULTILINE)  # Headers
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)  # Links
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove backslashes
    text = text.replace('\\', '')
    return text

def clean_text_for_pdf(text):
    """Clean and encode text for PDF compatibility"""
    text = clean_text_for_display(text)  # First remove markdown and special chars
    text = text.replace("–", "-").replace("—", "-")
    return text.encode("ascii", "ignore").decode()

def get_risk_description(risk_level):
    """Get description for a risk level"""
    descriptions = {
        1: "a focus on preserving capital with minimal risk and moderate returns",
        2: "a priority on safety with some attention to returns",
        3: "a balanced approach between risk and potential returns",
        4: "a focus on growth with acceptance of higher volatility",
        5: "a strong emphasis on growth potential with acceptance of significant volatility"
    }
    return descriptions.get(risk_level, "a balanced approach between risk and potential returns")

def format_esg_score(esg_score):
    """Format ESG score to be user-friendly"""
    if esg_score is None or str(esg_score).lower() == 'none' or str(esg_score).lower() == 'n/a':
        return "N/A", "Data not available"
    
    try:
        score_float = float(esg_score)
        if score_float >= 80:
            rating = "Excellent"
        elif score_float >= 60:
            rating = "Good"
        elif score_float >= 40:
            rating = "Average"
        else:
            rating = "Below Average"
        
        return f"{int(score_float)}", rating
    except:
        return str(esg_score), ""

# =========================================================================
# 2. EMAIL & PDF GENERATION
# =========================================================================

# Email Configuration
EMAIL_SENDER = "Investmentguideprogramming@gmx.de"
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = "mail.gmx.net"
SMTP_PORT = 587

def send_email_with_pdf(receiver_email, pdf_filename):
    """Send email with the PDF investment report attached"""
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

def explain_recommendations_with_gpt(profile, recommendations, name):
    """Generate personalized explanation using AI with improved reliability and cleaning"""
    risk_level = profile.get("risk_level", 3)
    risk_label = RISK_LEVEL_NAME.get(risk_level, "Balanced")
    
    # Group recommendations by region
    grouped = defaultdict(list)
    for r in recommendations:
        grouped[r["region"]].append(r)
    
    # Format recommendations for the API
    formatted_regions = []
    for region in ["Europe", "North America", "Emerging Markets"]:
        if region in grouped:
            regional_recs = [
                f"- {r['ticker']} ({PRODUCT_INFO.get(r['ticker'], (r['ticker'], r['asset_class']))[0]}), "
                f"Asset Type: {r['asset_class']}, "
                f"ESG Score: {r.get('esgScore', 'N/A')}, "
                f"Overall Rating: {r.get('final_score', 0):.2f}"
                for r in grouped[region][:3]
            ]
            formatted_regions.append(f"Region {region}:\n" + "\n".join(regional_recs))
    
    all_formatted_recs = "\n\n".join(formatted_regions)

    # Include profile elements in the prompt
    profile_elements = []
    for q_id, q_text in [(k, v["text"]) for k, v in enumerate(QUESTIONNAIRE) if k in profile]:
        if q_id in profile:
            profile_elements.append(f"{q_text}: {profile[q_id]}")
    
    profile_summary = "\n".join(profile_elements)

    # Prompt with clear instructions
    prompt = f"""
You are a friendly financial advisor helping a beginner named {name}.
Write a comprehensive and personalized explanation for the following investment profile:

Risk Level: {risk_level} – {risk_label}
IMPORTANT: This risk level of {risk_level} must be explicitly mentioned and explained in your response.

Complete Profile Information:
{profile_summary}

Recommended Investments:
{all_formatted_recs}

Instructions:
1. Start with a warm personal greeting to {name}
2. Explain what their risk level ({risk_level} - {risk_label}) means specifically for them
3. Connect their investment timeframe to the recommended investments
4. Explain how these specific recommendations match their risk/return preferences
5. Highlight the importance of regional diversification across Europe, North America, and Emerging Markets
6. If they showed interest in ESG investing, explain what the ESG scores mean
7. DO NOT include implementation steps or "next steps" as these will be provided separately
8. Write in a friendly, conversational tone avoiding financial jargon
9. End with encouragement appropriate for their experience level
10. The entire explanation should be 4-8 paragraphs

IMPORTANT FORMAT INSTRUCTIONS:
- Use plain text only with absolutely NO formatting characters of any kind
- Do NOT use backticks (`) anywhere in your response
- Do NOT use markdown formatting, asterisks, or any special characters
- Do NOT use HTML tags or any code formatting
- Do NOT use section headers with # symbols
- Do NOT use triple backticks (```)
- If mentioning an ESG score of "None", explain it means data isn't available
- Write your response in English only
- Use simple paragraph formatting with blank lines between paragraphs
"""

    # Try multiple models with fallback
    for attempt, model in enumerate([
        "deepseek/deepseek-prover-v2:free",
        "gpt-4o-mini",
        "claude-3-sonnet-20240229"
    ]):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful and friendly financial assistant for absolute beginners. Provide personalized, clear advice without financial jargon or any special formatting."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Check if response has expected structure
            if hasattr(response, 'choices') and len(response.choices) > 0 and hasattr(response.choices[0], 'message') and hasattr(response.choices[0].message, 'content'):
                # Clean up any markdown headers and formatting
                result = clean_text_for_display(response.choices[0].message.content)
                return result
        except Exception as e:
            print(f"API Error with model {model}: {str(e)}")
            if attempt >= 2:  # Last attempt
                # Create a simple generic response
                return (f"Hello {name},\n\nBased on your questionnaire responses, we've identified your risk profile "
                       f"as Level {risk_level} - {risk_label}. This risk level helps determine the balance of stability and growth potential in your investments.\n\n"
                       f"We've selected investments matching your level {risk_level} profile across Europe, North America, and Emerging Markets. "
                       f"Our recommendations are designed to balance risk and potential returns according to your {risk_label} profile.\n\n"
                       f"Remember that your risk level {risk_level} - {risk_label} means {get_risk_description(risk_level)}.\n\n"
                       f"We wish you success on your investment journey!")
    
    # If we get here, all attempts failed
    return (f"Hello {name},\n\nBased on your questionnaire responses, we've identified your risk profile "
           f"as Level {risk_level} - {risk_label}. This risk level helps determine the balance of stability and growth potential in your investments.\n\n"
           f"We've selected investments matching your level {risk_level} profile across Europe, North America, and Emerging Markets. "
           f"Our recommendations are designed to balance risk and potential returns according to your {risk_label} profile.\n\n"
           f"Remember that your risk level {risk_level} - {risk_label} means {get_risk_description(risk_level)}.\n\n"
           f"We wish you success on your investment journey!")

def generate_pdf_report_with_api(profile, recommendations, explanation_text, name="investment_report"):
    """Generate fully personalized PDF report with improved structure and no redundant sections"""
    risk_level = profile.get('risk_level', 3)
    risk_label = RISK_LEVEL_NAME.get(risk_level, "Balanced")
    
    # Clean the explanation text to ensure no markdown or special characters
    clean_explanation = clean_text_for_pdf(explanation_text)
    
    # Generate action steps with API - this will be the ONLY next steps section
    next_steps_prompt = f"""
You are a financial advisor helping a beginner with investment recommendations.
Create a comprehensive action plan with 5 specific steps for a risk profile of Level {risk_level} - {risk_label}.
Each step should be practical, actionable, and appropriate for a beginner investor.

For each step:
1. Start with a short, clear action title (3-5 words)
2. Follow with 1-2 sentences explaining what to do and why it matters
3. Each step should be self-contained and specific

IMPORTANT: 
- Address the reader directly using "you" (not third person)
- Format as a clean numbered list from 1-5
- Do not include ANY formatting, markdown, or special characters

EXAMPLES OF GOOD STYLE:
- "1. Open a Brokerage Account: Choose a broker with low fees and an easy-to-use platform. This will be your gateway to purchasing investments."
- "2. Set Up Regular Investments: Establish automatic monthly transfers to benefit from dollar-cost averaging and make investing a habit."

Do not include ANY formatting, markdown, or special characters in your response.
"""
    
    try:
        next_steps_response = client.chat.completions.create(
            model="deepseek/deepseek-prover-v2:free",
            messages=[
                {"role": "system", "content": "You provide clear, concise financial advice for beginners without any formatting or special characters."},
                {"role": "user", "content": next_steps_prompt}
            ]
        )
        next_steps_text = next_steps_response.choices[0].message.content
        # Clean the text and split into steps
        next_steps_text = clean_text_for_display(next_steps_text)
        next_steps = [step.strip() for step in next_steps_text.split('\n') if step.strip() and any(digit in step[:2] for digit in "12345")]
        
        # If we didn't get valid steps, use improved default steps
        if len(next_steps) < 3:
            next_steps = [
                "1. Open a Brokerage Account: Choose a reputable online broker with low fees and an easy-to-use platform.",
                "2. Fund Your Account: Transfer your initial investment funds and set up recurring deposits.",
                "3. Purchase Recommended Securities: Buy the ETFs, bonds, or stocks suggested in this report.",
                "4. Set Up Automatic Investments: Create a monthly investment plan to benefit from dollar-cost averaging.",
                "5. Schedule Regular Reviews: Review your portfolio performance quarterly and adjust as needed."
            ]
    except Exception as e:
        print(f"API Error for next steps: {str(e)}")
        next_steps = [
            "1. Open a Brokerage Account: Choose a reputable online broker with low fees and an easy-to-use platform.",
            "2. Fund Your Account: Transfer your initial investment funds and set up recurring deposits.",
            "3. Purchase Recommended Securities: Buy the ETFs, bonds, or stocks suggested in this report.",
            "4. Set Up Automatic Investments: Create a monthly investment plan to benefit from dollar-cost averaging.",
            "5. Schedule Regular Reviews: Review your portfolio performance quarterly and adjust as needed."
        ]
    
    # Create the PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("DejaVu", "", "Fonts/DejaVuSans.ttf", uni=True)
    
    # ----- TITLE PAGE -----
    pdf.set_font("DejaVu", size=18)
    pdf.cell(200, 15, txt=f"INVESTMENT REPORT", ln=True, align="C")
    pdf.set_font("DejaVu", size=14)
    pdf.cell(200, 10, txt=f"Prepared for {name}", ln=True, align="C")
    
    # Add prominent risk level display
    pdf.set_font("DejaVu", size=12)
    pdf.cell(200, 10, txt=f"Risk Profile: Level {risk_level} - {risk_label}", ln=True, align="C")
    
    # Add date with some spacing
    today = datetime.now().strftime("%B %d, %Y")
    pdf.set_font("DejaVu", size=10)
    pdf.cell(200, 10, txt=f"Generated on: {today}", ln=True, align="C")
    
    # Add a divider line
    pdf.line(30, pdf.get_y() + 5, 180, pdf.get_y() + 5)
    pdf.ln(15)

    # ----- SECTION 1: RISK PROFILE -----
    pdf.set_fill_color(240, 240, 240)  # Light gray background
    pdf.set_font("DejaVu", size=14)
    pdf.cell(0, 10, txt="1. YOUR INVESTMENT RISK PROFILE", ln=True, fill=True)
    pdf.ln(5)
    
    pdf.set_font("DejaVu", size=11)
    pdf.cell(0, 8, f"Risk Level: {risk_level} - {risk_label}", ln=True)
    
    # Use first paragraph from clean explanation
    pdf.set_font("DejaVu", size=10)
    risk_paragraphs = clean_explanation.split('\n\n')
    if len(risk_paragraphs) >= 2:
        pdf.multi_cell(0, 6, "\n\n".join(risk_paragraphs[:2]))
    else:
        pdf.multi_cell(0, 6, clean_explanation)
    pdf.ln(5)

    # ----- SECTION 2: KEY FACTORS -----
    pdf.set_font("DejaVu", size=14)
    pdf.cell(0, 10, txt="2. KEY FACTORS IN YOUR PROFILE", ln=True, fill=True)
    pdf.ln(5)
    
    key_questions = {
        1: "Investment Timeframe",
        2: "Market Volatility Comfort",
        4: "Expected Annual Return",
        8: "Risk vs. Reward Attitude",
        13: "ESG Investment Interest"
    }
    
    pdf.set_font("DejaVu", size=10)
    for q_id, q_label in key_questions.items():
        if q_id in profile:
            pdf.cell(0, 8, f"• {q_label}: {profile[q_id]}", ln=True)
    pdf.ln(5)

    # ----- SECTION 3: INVESTMENT STRATEGY -----
    pdf.set_font("DejaVu", size=14)
    pdf.cell(0, 10, txt="3. YOUR PERSONALIZED INVESTMENT STRATEGY", ln=True, fill=True)
    pdf.ln(5)
    
    pdf.set_font("DejaVu", size=10)
    pdf.multi_cell(0, 6, clean_explanation)
    pdf.ln(5)

    # ----- SECTION 4: RECOMMENDED INVESTMENTS -----
    pdf.set_font("DejaVu", size=14)
    pdf.cell(0, 10, txt="4. YOUR RECOMMENDED INVESTMENTS", ln=True, fill=True)
    pdf.ln(5)

    # Group recommendations by region
    grouped = defaultdict(list)
    for r in recommendations:
        grouped[r["region"]].append(r)

    # Show recommendations by region
    for region_idx, region in enumerate(["Europe", "North America", "Emerging Markets"]):
        if region in grouped:
            # Add page break before new regions (except the first)
            if region_idx > 0:
                pdf.add_page()
                
            pdf.set_font("DejaVu", size=12)
            pdf.set_text_color(0, 51, 102)  # Dark blue for region headers
            pdf.cell(0, 10, f"Region: {region}", ln=True)
            pdf.set_text_color(0, 0, 0)  # Reset to black
            pdf.set_font("DejaVu", size=10)
            
            # Create consistent box sizing to ensure uniform appearance
            box_height = 30  # Fixed height for all recommendation boxes
            
            for rec in grouped[region]:
                # Check if we're close to the bottom of the page
                if pdf.get_y() > 250:  # If less than 47 points left, add a new page
                    pdf.add_page()
                
                name, asset_type = PRODUCT_INFO.get(rec["ticker"], ("Unknown", rec["asset_class"]))
                
                # Create a highlight box for each recommendation with consistent size
                pdf.set_fill_color(248, 249, 250)  # Very light gray
                box_y = pdf.get_y()
                pdf.rect(pdf.get_x(), box_y, 180, box_height, style='F')
                
                # Position cursor inside the box
                pdf.set_xy(pdf.get_x() + 5, box_y + 2)
                
                # Bold ticker and name
                pdf.set_font("DejaVu", size=10)
                pdf.cell(0, 6, f"{rec['ticker']} - {name}", ln=True)
                
                # Investment details with consistent indentation and spacing
                pdf.set_xy(pdf.get_x() + 10, pdf.get_y())
                pdf.cell(0, 6, f"Type: {asset_type}", ln=True)
                
                # Show ESG score if user is interested in ESG
                esg_interested = profile.get(13, "") == "Yes"
                if esg_interested:
                    esg_value = rec.get('esgScore', 'N/A')
                    pdf.set_xy(pdf.get_x() + 10, pdf.get_y())
                    # Improved ESG score display
                    if esg_value == 'None' or esg_value is None:
                        pdf.cell(0, 6, f"ESG Score: N/A - Data unavailable", ln=True)
                    else:
                        # Format as integer if possible
                        try:
                            esg_display = f"{int(float(esg_value))}"
                            # Add score quality indicator
                            if float(esg_value) >= 80:
                                esg_display += " (Excellent)"
                            elif float(esg_value) >= 60:
                                esg_display += " (Good)"
                            elif float(esg_value) >= 40:
                                esg_display += " (Average)"
                            else:
                                esg_display += " (Below Average)"
                        except:
                            esg_display = str(esg_value)
                        pdf.cell(0, 6, f"ESG Score: {esg_display}", ln=True)
                
                # Rating display with meaning
                pdf.set_xy(pdf.get_x() + 10, pdf.get_y())
                rating = rec.get('final_score', 0)
                rating_text = "Excellent Match" if rating >= 0.8 else (
                            "Strong Match" if rating >= 0.6 else (
                            "Good Match" if rating >= 0.4 else (
                            "Acceptable Match" if rating >= 0.2 else "Minimal Match")))
                pdf.cell(0, 6, f"Overall Rating: {rating:.2f} ({rating_text})", ln=True)
                
                # Reset position after the box
                pdf.set_xy(pdf.get_x(), box_y + box_height)
                pdf.ln(5)  # Add consistent spacing between boxes

    # ----- SECTION 5: ACTION PLAN (NEXT STEPS) -----
    pdf.add_page()  # Start action plan on a new page
    pdf.set_font("DejaVu", size=14)
    pdf.cell(0, 10, txt="5. YOUR ACTION PLAN", ln=True, fill=True)
    pdf.ln(5)
    
    pdf.set_font("DejaVu", size=10)
    pdf.multi_cell(0, 6, "Follow these steps to implement your investment strategy:")
    pdf.ln(3)
    
    # Format the action steps with better spacing and structure
    for step in next_steps:
        # Try to separate the title from the description if possible
        if ': ' in step and step[0].isdigit():
            step_num, rest = step.split(' ', 1)
            if ': ' in rest:
                title, description = rest.split(': ', 1)
                pdf.set_font("DejaVu", size=11)
                pdf.cell(0, 8, f"{step_num} {title}", ln=True)
                pdf.set_font("DejaVu", size=10)
                pdf.set_xy(pdf.get_x() + 15, pdf.get_y())
                pdf.multi_cell(0, 6, f"{description}")
            else:
                pdf.multi_cell(0, 6, step)
        else:
            pdf.multi_cell(0, 6, step)
        pdf.ln(3)
    
    # ----- DISCLAIMER -----
    pdf.ln(5)
    pdf.line(30, pdf.get_y(), 180, pdf.get_y())  # Add horizontal line
    pdf.ln(5)
    pdf.set_font("DejaVu", size=8)
    pdf.set_text_color(100, 100, 100)  # Gray text for disclaimer
    pdf.multi_cell(0, 4, "DISCLAIMER: This investment report is for informational purposes only and does not constitute investment advice. Always consult with a licensed financial advisor before making investment decisions. Past performance is not indicative of future results.")

    # Generate the filename with user name to avoid confusion
    safe_name = name.replace(' ', '_').replace(',', '').replace('.', '')
    filename = f"{safe_name}_investment_report.pdf"
    pdf.output(filename)
    return filename

# =========================================================================
# 3. QUESTIONNAIRE EXPLANATIONS
# =========================================================================

# Dictionary of explanations for each question
question_explanations = {
    0: "Your investment objective guides the overall strategy we'll recommend.",
    1: "Your investment timeframe is crucial - generally, longer periods allow for higher-risk strategies.",
    2: "Market volatility (ups and downs) is normal, but your comfort level with it helps determine suitable investments.",
    3: "How you react to losses reveals your true risk tolerance and helps us find investments that won't cause you undue stress.",
    4: "Expected returns should be realistic - higher returns generally require taking on more risk.",
    5: "Investments that are easily converted to cash typically offer lower returns than those locked in for longer periods.",
    6: "This question helps us assess whether simpler or more complex investment products are suitable for you.",
    7: "The proportion of savings you invest affects how conservative or aggressive your strategy should be.",
    8: "This directly addresses your preference for balancing potential gains against possible losses.",
    9: "Stable income may allow for more investment risk, while uncertain income might require more conservative approaches.",
    10: "Major upcoming expenses mean you should keep more money in accessible, low-risk investments.",
    11: "Your current cash position helps us understand your liquidity needs and risk capacity.",
    12: "Your response shows how you might behave during market downturns, which helps us recommend suitable investments.",
    13: "ESG investing considers environmental, social, and governance factors alongside financial returns.",
    14: "'Investing with borrowed money' means investing more than you actually have - which increases both potential gains and risks."
}

# =========================================================================
# 4. STREAMLIT APP SETUP
# =========================================================================

st.set_page_config(page_title="Beginner Investment Advisor", layout="wide")

# CSS for a more user-friendly design
st.markdown("""
<style>
    .stButton button {
        font-size: 1.1em; 
        padding: 0.5em 1em;
    }
    .stRadio label {
        font-size: 1.05em;
        margin-top: 0.5em;
    }
    .question-container {
        background-color: #f5f8ff; 
        padding: 2em;
        border-radius: 10px;
        margin-bottom: 1.5em;
    }
    .result-box {
        background-color: #f0f8f4;
        padding: 1.5em;
        border-radius: 8px;
        margin-bottom: 1em;
    }
    .info-box {
        background-color: #e1f5fe;
        padding: 1em;
        border-radius: 5px;
        margin: 1em 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "name" not in st.session_state:
    st.session_state.name = ""
if "current_question" not in st.session_state:
    st.session_state.current_question = 0
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "questionnaire_complete" not in st.session_state:
    st.session_state.questionnaire_complete = False
if "email_sent" not in st.session_state:
    st.session_state.email_sent = False
if "report_filename" not in st.session_state:
    st.session_state.report_filename = ""
if "gpt_explanation" not in st.session_state:
    st.session_state.gpt_explanation = None

# =========================================================================
# 5. APP FLOW
# =========================================================================

# Welcome screen
if not st.session_state.name:
    st.title("Welcome to the Beginner Investment Advisor")
    st.markdown("""
    <div class="info-box">
    <h3>🚀 Start Your Investment Journey</h3>
    <p>This assistant will help you find the right entry into the world of investments. 
    Through a few simple questions, we'll determine your risk profile and give you suitable investment recommendations.</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form(key="name_form", clear_on_submit=True):
        name_input = st.text_input("Please enter your name:")
        email_input = st.text_input("And your email address for your personal report:")
        
        # Add email verification message
        st.info("⚠️ Please double-check your email address for accuracy. Your personalized investment report will be sent to this address.")
        
        start_clicked = st.form_submit_button("Start")
        if start_clicked and name_input.strip() and email_input.strip():
            st.session_state.name = name_input.strip()
            st.session_state.email = email_input.strip()
            st.rerun()

# Questionnaire
elif not st.session_state.questionnaire_complete:
    st.title(f"Welcome, {st.session_state.name}!")
    current_question_index = st.session_state.current_question
    question = QUESTIONNAIRE[current_question_index]
    
    # Progress bar
    progress = (current_question_index) / (len(QUESTIONNAIRE) - 1)
    st.progress(progress)
    
    with st.form(key=f"question_form_{current_question_index}", clear_on_submit=True):
        st.markdown(f"""
        <div class="question-container">
            <span style='font-size:1.5em; font-weight:bold; color:#1a237e;'>Question {current_question_index + 1} of {len(QUESTIONNAIRE)}</span><br>
            <span style='font-size:1.2em; font-weight:bold; color:#222;'>{question['text']}</span>
            <p style='font-size:0.9em; color:#666; margin-top:0.5em;'>Choose the option that best fits you.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show explanation for each question
        st.info(question_explanations[current_question_index])
        
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
            if current_question_index + 1 < len(QUESTIONNAIRE):
                next_clicked = st.form_submit_button("Next")
            else:
                next_clicked = st.form_submit_button("Show Results")
                
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

# Show results
else:
    answers = st.session_state.answers
    
    st.title(f"Thank you, {st.session_state.name}!")
    st.write("✅ You have completed the questionnaire!")
    
    # Reset stored explanation if restarting the questionnaire
    if "restart_questionnaire" in st.session_state and st.session_state.restart_questionnaire:
        st.session_state.gpt_explanation = None
        st.session_state.restart_questionnaire = False
    
    # Loading animation
    with st.spinner("⏳ Please be patient while we prepare your personalized results..."):
        try:
            # First get the recommendation results
            result = generate_full_recommendation(st.session_state.answers)
            
            # Then create the profile with the accurate risk level from the recommendation
            profile = map_answers_to_profile(answers)
            profile["risk_level"] = result["risk_level"]  # Use the enhanced risk level
            risk_level = result["risk_level"]  # For display
        except Exception as e:
            st.error(f"Error generating recommendations: {str(e)}")
            st.stop()
    
    primary = result["primary_etf"]
    recommendations = result["recommendations"]
    
    # Overview in a box container
    st.markdown("""
    <div class="result-box">
        <h2>📊 Your Investment Summary</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Risk profile with explanation
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Your Risk Profile")
        st.markdown(f"""
        **Risk Level:** {risk_level} – *{RISK_LEVEL_NAME[risk_level]}*  
        **Primary Recommendation:** `{primary['ticker']}`
        """)
    with col2:
        # Simple explanation of the risk profile
        risk_explanations = {
            1: "Very safety-oriented with a focus on capital preservation. Low risk, moderate returns.",
            2: "Safety-oriented with a slight return orientation. Low to medium risk.",
            3: "Balanced relationship between safety and return. Medium risk.",
            4: "Return-oriented with increased risk tolerance. Higher risk for better return potential.",
            5: "Strongly return-oriented with high risk tolerance. Highest risk for maximum return potential."
        }
        st.info(risk_explanations.get(risk_level, "No risk profile available."))
    
    # Sort and display recommendations by region
    grouped = defaultdict(list)
    for r in recommendations:
        grouped[r["region"]].append(r)
    
    # Show recommendations by region
    for region in ["Europe", "North America", "Emerging Markets"]:
        if region in grouped:
            st.subheader(f"🌍 {region}")
            for r in grouped[region]:
                name, asset_type = PRODUCT_INFO.get(r["ticker"], ("Unknown", r["asset_class"]))
                
                # Improved ESG score display
                esg_score = r.get('esgScore', 'N/A')
                esg_display, esg_rating = format_esg_score(esg_score)
                if esg_rating:
                    esg_display = f"{esg_display} ({esg_rating})"
                esg_tooltip = "Data not available" if esg_display == "N/A" else "Environmental, Social, and Governance score (0-100)"
                
                # Format the overall rating with clear meaning
                rating_score = r.get('final_score', 0)
                if rating_score >= 0.8:
                    rating_display = f"{rating_score:.2f} (Excellent Match)"
                elif rating_score >= 0.6:
                    rating_display = f"{rating_score:.2f} (Strong Match)"
                elif rating_score >= 0.4:
                    rating_display = f"{rating_score:.2f} (Good Match)"
                elif rating_score >= 0.2:
                    rating_display = f"{rating_score:.2f} (Acceptable Match)"
                else:
                    rating_display = f"{rating_score:.2f} (Minimal Match)"
                
                # Create the recommendation box with improved display
                st.markdown(f"""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 10px;">
                    <h4 style="margin-top: 0;">{r["ticker"]} - {name}</h4>
                    <p><strong>Type:</strong> {asset_type}</p>
                    <p><strong>ESG Score:</strong> {esg_display} <span style="font-size: 0.9em; color: #6c757d;">({esg_tooltip})</span></p>
                    <p><strong>Overall Rating:</strong> {rating_display}</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Generate the personalized explanation with better error handling
    try:
        with st.spinner("Generating your personalized explanation..."):
            # Use saved explanation or generate a new one
            if st.session_state.gpt_explanation is None:
                gpt_text = explain_recommendations_with_gpt(profile, recommendations, st.session_state.name)
                # Clean the text before storing it
                gpt_text = clean_text_for_display(gpt_text)
                st.session_state.gpt_explanation = gpt_text
            else:
                gpt_text = st.session_state.gpt_explanation
            
        st.subheader("Your Personalized Investment Explanation")
        
        # Use st.write which handles newlines properly without HTML
        st.write(gpt_text)
    except Exception as e:
        st.error(f"Error generating explanation: {str(e)}")
        # Generate a fallback explanation
        if st.session_state.gpt_explanation is None:
            gpt_text = explain_recommendations_with_gpt(profile, recommendations, st.session_state.name)
            gpt_text = clean_text_for_display(gpt_text)
            st.session_state.gpt_explanation = gpt_text
        else:
            gpt_text = st.session_state.gpt_explanation
        st.write(gpt_text)
    
    # Understanding section with detailed explanations
    st.subheader("Understanding Your Results")
    
    # Expander 1: How the Overall Rating is Calculated
    with st.expander("📈 How the Overall Rating is Calculated"):
        st.markdown("""
        ## Understanding the Overall Rating
        
        The overall rating (from 0 to 1) is a comprehensive score that measures how well each investment matches your specific needs and risk profile. 
        
        ### Factors Considered in the Rating
        
        Your rating is calculated based on several key financial metrics:
        
        1. **EV/EBITDA ratio**: A valuation metric that compares a company's enterprise value to its earnings before interest, taxes, depreciation, and amortization
           - Lower values are generally better
           - More heavily weighted for conservative investors
           
        2. **Free Cash Flow Yield**: Shows how much cash a company generates relative to its market capitalization
           - Higher values are better
           - More heavily weighted for growth-oriented investors
           
        3. **Volatility**: Measures how much the price of an investment fluctuates over time
           - Lower volatility is preferred for conservative investors
           - Higher volatility may be acceptable for aggressive investors seeking growth
           
        4. **ESG Score**: Evaluates environmental, social, and governance factors
           - Given higher weight if you expressed interest in sustainable investing
           
        5. **Dividend Yield**: The annual dividend payment relative to the share price (especially for income-focused investors)
           - Higher weight for those seeking regular income
        
        ### How Your Profile Affects the Rating
        
        The weighting of these factors changes based on your risk level:
        
        - **Defensive (Level 1)**: Emphasizes low volatility and stability metrics
        - **Conservative (Level 2)**: Balances stability with modest growth potential 
        - **Balanced (Level 3)**: Even distribution across growth and stability factors
        - **Growth Tilt (Level 4)**: Emphasizes growth metrics with moderate stability
        - **Aggressive (Level 5)**: Strongly emphasizes growth potential
        
        ### Understanding the Score Range
        
        - **0.80-1.00**: Excellent match for your profile
        - **0.60-0.79**: Strong match
        - **0.40-0.59**: Good match
        - **0.20-0.39**: Acceptable match
        - **0.00-0.19**: Minimal match
        
        ### Further Adjustments
        
        The system also makes adjustments based on:
        
        - Your investment objectives (wealth accumulation, income, or preservation)
        - Your liquidity needs
        - Your investment experience
        - Regional characteristics (developed vs. emerging markets)
        - Asset class characteristics (bonds, ETFs, stocks)
        
        The final result is a personalized rating that helps identify investments that best align with your unique financial situation and goals.
        """)
    
    # Expander 2: Understanding the ESG Scores
    with st.expander("🌿 Understanding the ESG Scores"):
        st.markdown("""
        ## Understanding the ESG Scores
        
        ESG scores range from 0-100 and measure how well a company or investment performs on:
        
        - **Environmental factors**: Climate impact, resource usage, pollution, etc.
        - **Social factors**: Labor practices, community relations, human rights, etc.
        - **Governance factors**: Board structure, executive compensation, ethics, etc.
        
        ### Score Ranges
        
        - **80-100**: Excellent ESG practices, industry leaders in sustainability
        - **60-79**: Strong ESG practices, above average performance
        - **40-59**: Average ESG performance, some strengths and weaknesses
        - **20-39**: Below average ESG practices, significant room for improvement
        - **0-19**: Poor ESG performance, substantial risks or issues
        
        ### When You See "N/A"
        
        If you see "N/A" for an ESG score, this does NOT mean the investment has poor ESG practices. It simply means:
        
        - ESG data is not available for this particular investment
        - The company may not yet be covered by major ESG rating agencies
        - The investment might be too new to have established ESG ratings
        - For some ETFs or smaller companies, comprehensive ESG analysis may not exist
        
        This is common for smaller companies, certain regions, or specialized investments. In these cases, you may want to research the company's sustainability practices directly if ESG factors are important to you.
        
        ### Regional Context
        
        - European investments typically have higher ESG scores (average 60-75)
        - North American investments have moderate ESG scores (average 55-65)
        - Emerging Markets investments often have lower ESG scores (average 45-55)
        
        ### Asset Type Differences
        
        - ESG-focused ETFs generally have the highest scores (70-95)
        - Green bonds often score well (65-90)
        - Individual stocks vary widely based on company practices
        
        ### Why ESG Matters
        
        - **Risk management**: Companies with poor ESG practices may face regulatory issues, fines, or reputational damage
        - **Long-term performance**: Some studies suggest companies with strong ESG practices may outperform over the long term
        - **Impact alignment**: Allows you to invest according to your values
        - **Future-proofing**: Companies addressing sustainability challenges may be better positioned for the future economy
        
        ### ESG Labels and Indicators
        
        Look for these indicators of strong ESG investments:
        - Labeled as "ESG", "SRI" (Socially Responsible Investing), or "Sustainable"
        - Part of sustainability indices (FTSE4Good, Dow Jones Sustainability Index)
        - Certified B Corporations
        - Green bond certification
        """)
    
    # Email and PDF report with resend option
    st.markdown("""
    <div class="info-box">
        <h3>📧 Get Your Detailed Report</h3>
        <p>We can send you a detailed report with all recommendations and explanations via email.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if email has already been sent
    if st.session_state.email_sent:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.success("Report has been sent to your email!")
            st.info("If you don't see the email, please check your spam or junk folder. The email comes from 'Investmentguideprogramming@gmx.de'")
        with col2:
            # Add resend button
            if st.button("Resend Email"):
                try:
                    send_email_with_pdf(st.session_state.email, st.session_state.report_filename)
                    st.success("Report has been resent to your email!")
                except Exception as e:
                    st.error(f"Error sending email: {str(e)}")
    else:
        if st.button("Get Detailed Report by Email"):
            try:
                # Use the stored explanation rather than generating a new one
                explanation_text = st.session_state.gpt_explanation
                
                # Use the improved PDF generator
                filename = generate_pdf_report_with_api(profile, recommendations, explanation_text, st.session_state.name)
                send_email_with_pdf(st.session_state.email, filename)
                st.success("Report sent to your email!")
                
                # Save state for resend option
                st.session_state.email_sent = True
                st.session_state.report_filename = filename
                st.rerun()
            except Exception as e:
                st.error(f"Error sending email: {str(e)}")
    
    # Helpful Tips for Beginners 
    with st.expander("📚 Helpful Tips for Beginners"):
        st.markdown("""
        ## Understanding Your Investment Options
        
        ### Types of Financial Assets
        
        #### ETFs (Exchange Traded Funds)
        ETFs are baskets of securities traded on stock exchanges like individual stocks. They offer:
        - **Diversification**: One ETF can contain hundreds of stocks or bonds
        - **Low costs**: Generally lower fees than mutual funds
        - **Flexibility**: Can be bought and sold throughout the trading day
        - **Tax efficiency**: Typically generate fewer capital gains than mutual funds
        - **Good for**: Most investors, especially beginners seeking diversification
        
        #### Bonds
        Bonds are loans to governments or corporations that pay interest over time:
        - **Income generation**: Regular interest payments (called coupons)
        - **Lower volatility**: Generally more stable than stocks
        - **Capital preservation**: Return of principal at maturity date
        - **Different types**: Government bonds, corporate bonds, municipal bonds
        - **Good for**: Conservative investors, retirees, or those seeking income
        
        #### Individual Stocks
        Stocks represent ownership in specific companies:
        - **Growth potential**: Can offer higher returns than ETFs or bonds
        - **Higher risk**: More volatile with potentially larger losses
        - **No diversification**: Performance tied to single companies
        - **Control**: You choose specific companies to invest in
        - **Good for**: More experienced investors willing to research companies
        
        ### ESG Investing
        ESG stands for Environmental, Social, and Governance. ESG scores assess how well a company performs in these areas. Higher scores indicate better sustainability practices.
        
        ### How to Start Investing
        1. Open an account with an online bank or broker
        2. Transfer an amount you want to start with
        3. Buy the recommended investments according to your risk profile
        4. Invest regularly (e.g., monthly) a fixed amount (savings plan)
        
        ### Important Terms
        - **Volatility**: How much an investment's price fluctuates (higher = more risk)
        - **Yield**: Income returned on an investment (dividends, interest)
        - **Diversification**: Spreading investments to reduce risk
        - **Asset allocation**: How your money is divided between different types of investments
        
        ### Important Note
        Investing involves risks. Inform yourself well and only invest money that you don't need in the short term.
        """)