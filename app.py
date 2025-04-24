import streamlit as st

st.title("Beginner Investment Advisor")
st.write("Welcome! This tool gives simple investment guidance for beginners.")

st.header("Step 1: What's your experience?")
experience = st.selectbox("Choose one:", ["None", "A little", "Some", "Advanced"])

st.header("Step 2: Investment Goal")
goal = st.radio("Your primary goal?", ["Grow wealth", "Save safely", "Both"])

if st.button("Get Recommendation"):
    if experience == "None" and goal == "Save safely":
        st.success("Try a savings account or beginner-friendly ETFs.")
    elif experience == "Advanced" and goal == "Grow wealth":
        st.success("You may explore individual stocks or mutual funds.")
    else:
        st.info("A balanced index fund may be a good starting point.")
