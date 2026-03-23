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

# Custom CSS matching Light Mode but with the Email Template's premium feel
st.markdown("""
<style>
    /* Force Light Mode Overrides for padding */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* Premium Gradient Header */
    .premium-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        padding: 30px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .premium-header h1 {
        color: white;
        margin: 0;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    .premium-header .date-badge {
        display: inline-block;
        background: rgba(255,255,255,0.2);
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: 600;
        margin-top: 10px;
    }
    
    /* Theme Card Styling */
    .streamlit-expanderHeader {
        font-weight: 700 !important;
        color: #1a1a2e !important;
    }
    
    /* Stat Text Enhancement */
    [data-testid="stMetricValue"] {
        color: #764ba2 !important;
        font-weight: 800 !important;
    }
    
    /* Quotes */
    .quote-box {
        background: #f8f9fa;
        border-left: 4px solid #f093fb;
        padding: 15px 20px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .quote-box p {
        margin: 0 0 10px 0;
        font-style: italic;
        color: #333;
    }
    .quote-badge {
        display: inline-block;
        background: rgba(240, 147, 251, 0.15);
        color: #d15ce0;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
    }
    
    /* Action Idea */
    .action-box {
        background: #ebfcf6;
        border: 1px solid #a7f3d0;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 12px;
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

    # Premium Gradient Header aligned with email
    st.markdown(f"""
    <div class="premium-header">
        <span style="font-size: 24px;">📊 Weekly Pulse</span>
        <h1>INDMoney User Sentiment Report</h1>
        <div class="date-badge">📅 {week_range}</div>
    </div>
    """, unsafe_allow_html=True)

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
        st.subheader("🏷️ Top Themes", anchor=False)
        for theme in themes_list:
            rank = theme.get("rank", "")
            name = theme.get("name", "Unknown")
            count = theme.get("review_count", 0)
            t_avg_rating = theme.get("avg_rating", 0.0)
            explanation = theme.get("explanation", "")
            
            with st.expander(f"{rank}. {name} ({count} reviews · {t_avg_rating} ★)"):
                st.write(explanation)
                
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🚀 Suggested Actions", anchor=False)
        for action in actions_list:
            title = action.get("title", "")
            rationale = action.get("rationale", "")
            st.markdown(f"""
            <div class="action-box">
                <strong style="color: #047857; font-size: 15px;">{title}</strong><br>
                <span style="color: #3f3f46; font-size: 14px;">{rationale}</span>
            </div>
            """, unsafe_allow_html=True)

    with main_col2:
        st.subheader("📊 Rating Distribution", anchor=False)
        if classified_data:
            df_ratings = pd.DataFrame(classified_data)
            rating_counts = df_ratings['rating'].value_counts().reset_index()
            rating_counts.columns = ['Rating', 'Count']
            rating_counts = rating_counts.sort_values('Rating', ascending=False)
            rating_counts['Rating'] = rating_counts['Rating'].astype(str) + " ★"
            
            # Using the email theme accent colors
            fig = px.bar(rating_counts, x='Count', y='Rating', orientation='h',
                         color_discrete_sequence=['#764ba2'])
            fig.update_layout(
                showlegend=False, margin=dict(l=0, r=0, t=0, b=0), height=250,
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            # Remove axis labels to keep it clean
            fig.update_xaxes(title_text="", showgrid=False, showticklabels=False)
            fig.update_yaxes(title_text="")
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("💬 What Users Are Saying", anchor=False)
        for quote in quotes_list:
            q_text = quote.get("quote", "")
            q_theme = quote.get("theme", "")
            q_rating = quote.get("rating", "")
            
            st.markdown(f"""
            <div class="quote-box">
                <p>❝ {q_text} ❞</p>
                <span class="quote-badge">★ {q_rating}</span> 
                <span style="font-size: 11px; color: #764ba2; font-weight: 500; margin-left: 5px;">{q_theme}</span>
            </div>
            """, unsafe_allow_html=True)

    # Sidebar: Review Explorer
    st.sidebar.title("🔍 Review Explorer")
    st.sidebar.markdown("Explore anonymised review metadata.")
    if classified_data:
        df_reviews = pd.DataFrame(classified_data)
        if 'text' in df_reviews.columns:
            df_reviews = df_reviews.drop(columns=['text'])
            
        if 'themes' in df_reviews.columns:
            df_reviews['themes'] = df_reviews['themes'].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
            
        st.sidebar.dataframe(df_reviews, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
