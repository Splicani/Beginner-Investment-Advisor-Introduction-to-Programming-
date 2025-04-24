import streamlit as st
import yfinance as yf
from typing import List, Dict, Tuple, Any
from MertCodev1 import (
    QUESTIONNAIRE,
    map_answers_to_profile,
    derive_asset_class,
    get_region_risk_etf,
    map_user_to_recommendations,
    PRODUCT_INFO
)

st.set_page_config(page_title="Beginner Investment Advisor", layout="wide")
st.title("📊 Beginner Investment Advisor")
st.write("Answer a few quick questions and get a personalized investment recommendation.")

# 1. Questionnaire Form
answers = {}
with st.form("questionnaire_form"):
    for q in QUESTIONNAIRE:
        answer = st.radio(q["text"], q["options"], key=q["id"])
        answers[q["id"]] = q["options"].index(answer)

    submitted = st.form_submit_button("Get Recommendation")

# 2. After submission
if submitted:
    profile = map_answers_to_profile(answers)
    asset_class = derive_asset_class(profile)
    rt_choice = answers[2]

    if rt_choice <= 1:
        risk_level = 1
    elif rt_choice == 2:
        risk_level = 3
    else:
        risk_level = 5

    st.subheader("🧑‍💼 Your Investor Profile")
    st.json(profile)

    st.write(f"**Asset Class Detected:** {asset_class.title()}")
    region = st.selectbox("🌍 Choose a region:", ["Europe", "North America", "Emerging Markets", "Any"])

    if region:
        result = {
            "investor_profile": profile,
            "risk_level":       risk_level,
            "primary_etf":      get_region_risk_etf(region, risk_level),
            "recommendations":  map_user_to_recommendations(region, asset_class, risk_level)
        }

        st.subheader("🌟 Primary ETF Recommendation")
        pef = result["primary_etf"]["ticker"]
        name, cls = PRODUCT_INFO.get(pef, (pef, asset_class.capitalize()))
        st.write(f"**{name}** ({cls}) `{pef}`")

        st.subheader("🏅 Top Investment Suggestions")
        top5 = result["recommendations"][:5]

        for itm in top5:
            tkr = itm["ticker"]
            name, cls = PRODUCT_INFO.get(tkr, (tkr, asset_class.capitalize()))
            st.markdown(
                f"- **{name}** ({cls}) `{tkr}`  \
                PE: `{itm.get('trailingPE','N/A')}`, DY: `{itm.get('dividendYield','N/A')}`, Score: `{itm.get('score',0):.2f}`"
            )

