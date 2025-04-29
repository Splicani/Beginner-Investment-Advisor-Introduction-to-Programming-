import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from LuisCodev1 import (
    QUESTIONNAIRE,
    map_answers_to_profile,
    derive_risk_level,
    get_region_risk_etf,
    generate_recommendation,
    PRODUCT_INFO,
    RISK_LEVEL_NAME
)

st.set_page_config(page_title="Beginner Investment Advisor", layout="wide")
st.title("📊 Beginner Investment Advisor")
st.write("Answer all questions below to receive a personalized investment recommendation.")

# Initialize session state
if "answers" not in st.session_state:
    st.session_state.answers = {}

with st.form("questionnaire_form"):
    for q in QUESTIONNAIRE:
        answer = st.radio(q["text"], q["options"], key=f"q_{q['id']}")
        st.session_state.answers[q["id"]] = q["options"].index(answer)

    submitted = st.form_submit_button("Get Recommendation")

if submitted:
    answers = st.session_state.answers
    profile = map_answers_to_profile(answers)
    rl = derive_risk_level(answers)

    st.subheader("🧑‍💼 Your Investor Profile")
    st.json(profile)

    st.write(f"**Risk Level:** {rl} ({RISK_LEVEL_NAME[rl]})")
    region = st.selectbox("🌍 Choose a region:", ["Europe", "North America", "Emerging Markets", "Any"])

    if region:
        result = generate_recommendation(answers, region)
        primary_etf = result["primary_etf"]["ticker"]
        name, cls = PRODUCT_INFO.get(primary_etf, (primary_etf, "ETF"))

        st.subheader("🌟 Primary ETF Recommendation")
        st.write(f"**{name}** ({cls}) `{primary_etf}`")

        st.subheader("🏅 Top Investment Suggestions")
        top5 = result["recommendations"][:5]

        # Convert top 5 to DataFrame for charts and download
        df = pd.DataFrame([{
            "Name": PRODUCT_INFO.get(itm["ticker"], (itm["ticker"], ""))[0],
            "Ticker": itm["ticker"],
            "Asset Class": itm["asset_class"].capitalize(),
            "EV/EBITDA": itm.get("ev_ebitda"),
            "FCF Yield": itm.get("fcf_yield"),
            "Volatility": itm.get("volatility"),
            "ESG Score": itm.get("esgScore"),
            "Score": itm.get("final_score", 0)
        } for itm in top5])

        st.dataframe(df)

        # Charts
        st.subheader("📈 Scores of Top Recommendations")
        fig, ax = plt.subplots()
        ax.bar(df["Name"], df["Score"], color="skyblue")
        ax.set_ylabel("Final Score")
        ax.set_title("Top 5 Scores")
        plt.xticks(rotation=45, ha="right")
        st.pyplot(fig)

        # Download button
        def convert_df(df):
            return df.to_csv(index=False).encode("utf-8")

        csv = convert_df(df)
        st.download_button(
            label="📥 Download Recommendations as CSV",
            data=csv,
            file_name="investment_recommendations.csv",
            mime="text/csv"
        )
