import streamlit as st
import json
import os
import pandas as pd
import plotly.express as px

# Configuration
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PULSE_FILE = os.path.join(DATA_DIR, "weekly_pulse.json")
CLASSIFIED_FILE = os.path.join(DATA_DIR, "reviews_classified.json")
EMAIL_FILE = os.path.join(DATA_DIR, "email_draft.html")

st.set_page_config(
    page_title="Weekly Pulse Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply some custom CSS for spacing and padding (similar to phase 6 light theme)
st.markdown("""
<style>
    .reportview-container {
        background-color: #fafafa;
    }
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

def load_data():
    if not os.path.exists(PULSE_FILE) or not os.path.exists(CLASSIFIED_FILE):
        return None, None
    
    with open(PULSE_FILE, "r", encoding="utf-8") as f:
        pulse_data = json.load(f)
        
    with open(CLASSIFIED_FILE, "r", encoding="utf-8") as f:
        classified_data = json.load(f)
        
    return pulse_data, classified_data

def main():
    st.title("📊 Weekly Pulse · User Sentiment")
    
    pulse_data, classified_data = load_data()
    
    if pulse_data is None or classified_data is None:
        st.warning("⚠️ Data files are missing. Please run the pipeline first to generate the necessary data.")
        st.info("Run `python main.py` in your terminal to collect reviews and generate the weekly pulse.")
        return

    # Extract meta information
    meta = pulse_data.get("meta", {})
    total_reviews = meta.get("total_reviews", pulse_data.get("total_reviews", 0))
    week_range = meta.get("week_range", pulse_data.get("week_range", ""))
    
    # Calculate avg rating from classified data
    if classified_data:
        avg_rating = sum(r.get("rating", 0) for r in classified_data) / len(classified_data)
    else:
        avg_rating = 0.0

    themes_list = pulse_data.get("themes", pulse_data.get("top_themes", []))
    quotes_list = pulse_data.get("quotes", pulse_data.get("user_quotes", []))
    actions_list = pulse_data.get("actions", pulse_data.get("action_ideas", []))

    st.markdown(f"**Date Range:** {week_range}")

    # Top Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Reviews", f"{total_reviews}")
    with col2:
        st.metric("Average Rating", f"{avg_rating:.1f} ★")
    with col3:
        st.metric("Top Themes", len(themes_list))
    with col4:
        email_status = "Draft Ready" if os.path.exists(EMAIL_FILE) else "Not Sent"
        st.metric("Email Status", email_status)
        
    st.divider()

    # Main Content Columns
    main_col1, main_col2 = st.columns([2, 1])

    with main_col1:
        st.subheader("🏷️ Top Themes")
        for theme in themes_list:
            rank = theme.get("rank", "")
            name = theme.get("name", "Unknown")
            count = theme.get("review_count", 0)
            t_avg_rating = theme.get("avg_rating", 0.0)
            explanation = theme.get("explanation", "")
            
            with st.expander(f"{rank}. {name} ({count} reviews · {t_avg_rating} ★)"):
                st.write(explanation)
                
        st.markdown("---")
        st.subheader("🚀 Suggested Actions")
        for action in actions_list:
            title = action.get("title", "")
            rationale = action.get("rationale", "")
            st.success(f"**{title}**\n\n{rationale}")

    with main_col2:
        st.subheader("📊 Rating Distribution")
        # Compute rating distribution
        if classified_data:
            df_ratings = pd.DataFrame(classified_data)
            rating_counts = df_ratings['rating'].value_counts().reset_index()
            rating_counts.columns = ['Rating', 'Count']
            rating_counts = rating_counts.sort_values('Rating', ascending=False)
            rating_counts['Rating'] = rating_counts['Rating'].astype(str) + " ★"
            
            fig = px.bar(rating_counts, x='Count', y='Rating', orientation='h',
                         color='Rating', color_discrete_sequence=px.colors.sequential.Purp)
            fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0), height=250)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("💬 What Users Are Saying")
        for quote in quotes_list:
            q_text = quote.get("quote", "")
            q_theme = quote.get("theme", "")
            q_rating = quote.get("rating", "")
            st.info(f"❝ {q_text} ❞\n\n**{q_rating} ★** · {q_theme}")

    # Sidebar: Review Explorer
    st.sidebar.title("🔍 Review Explorer")
    st.sidebar.markdown("Explore anonymised review metadata.")
    if classified_data:
        df_reviews = pd.DataFrame(classified_data)
        # Drop PII / raw text per rule P7.3
        if 'text' in df_reviews.columns:
            df_reviews = df_reviews.drop(columns=['text'])
            
        # Format themes if it's a list
        if 'themes' in df_reviews.columns:
            df_reviews['themes'] = df_reviews['themes'].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
            
        st.sidebar.dataframe(df_reviews, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
