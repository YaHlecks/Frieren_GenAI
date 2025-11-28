import streamlit as st
import pandas as pd
import pickle
import plotly.graph_objects as go
import os
import nltk
import datetime
from pandas.tseries.offsets import MonthBegin
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt

# -------------------------------
# App metadata / page config
# -------------------------------
st.set_page_config(page_title="Laboratorial", layout="wide", initial_sidebar_state="expanded")

# -------------------------------
# Ensure NLTK resources (download only once)
# -------------------------------
def ensure_nltk_resource(resource_name, download_name=None):
    try:
        nltk.data.find(resource_name)
    except LookupError:
        download_target = download_name or resource_name.split('/')[-1]
        nltk.download(download_target)

ensure_nltk_resource('tokenizers/punkt', 'punkt')
ensure_nltk_resource('corpora/stopwords', 'stopwords')

# -------------------------------
# Session state defaults
# -------------------------------
if 'page' not in st.session_state:
    st.session_state.page = 'Home'
if 'forecast_df' not in st.session_state:
    st.session_state.forecast_df = None
if 'selected_indicator' not in st.session_state:
    st.session_state.selected_indicator = 'LFPR_Total'
if 'nltk_ready' not in st.session_state:
    st.session_state.nltk_ready = True

# -------------------------------
# Constants and configuration
# -------------------------------
MODEL_DIR = 'models'
INDICATORS = {
    'LFPR_Total': 'Labor Force Participation Rate (Total)',
    'LFPR_Male': 'Labor Force Participation Rate (Male)',
    'LFPR_Female': 'Labor Force Participation Rate (Female)',
    'ER_Total': 'Employment Rate (Total)',
    'ER_Male': 'Employment Rate (Male)',
    'ER_Female': 'Employment Rate (Female)',
    'UR_Total': 'Unemployment Rate (Total)',
    'UR_Male': 'Unemployment Rate (Male)',
    'UR_Female': 'Unemployment Rate (Female)',
    'UER_Total': 'Underemployment Rate (Total)',
    'UER_Male': 'Underemployment Rate (Male)',
    'UER_Female': 'Underemployment Rate (Female)'
}

# -------------------------------
# Sidebar: navigation + theme
# -------------------------------
st.sidebar.markdown('# Navigation')
page = st.sidebar.radio('', ['Home', 'Predict', 'Results & Analysis'])
st.session_state.page = page
st.sidebar.markdown('---')

theme = st.sidebar.radio('Theme', ['Light', 'Dark'])

# theme colors
if theme == 'Light':
    BG_COLOR = '#FFFFFF'
    TEXT_COLOR = '#111111'
    ACCENT = '#2f80ed'
    GRID_COLOR = '#e6e6e6'
else:
    BG_COLOR = '#0f1720'
    TEXT_COLOR = '#ffffff'
    ACCENT = '#ecad29'
    GRID_COLOR = '#263238'

# -------------------------------
# CSS Styling
# -------------------------------
st.markdown(f"""
<style>
    .reportview-container {{ background: {BG_COLOR}; color: {TEXT_COLOR}; }}
    .stButton>button {{ background-color: {ACCENT}; color: white; border-radius: 8px; padding: 0.6rem 1rem; }}
    .stButton>button:hover {{ opacity: 0.9; }}
    .metric-card {{ background: transparent; border-radius: 12px; padding: 1rem; text-align: center; color: {TEXT_COLOR}; }}
    h1, h2, h3 {{ color: {ACCENT}; }}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Helper: load model safely (cached)
# -------------------------------
@st.cache_resource
def load_model(indicator_key: str):
    filename = f"sarimax_model_{indicator_key}.pkl"
    path = os.path.join(MODEL_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model file not found: {path}")
    with open(path, 'rb') as f:
        model = pickle.load(f)
    return model

# -------------------------------
# Chart helpers
# -------------------------------
def stylish_chart(x, y, y_label):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y, mode='lines+markers',
        line=dict(width=3),
        marker=dict(size=6),
        fill='tozeroy', fillcolor='rgba(47,128,237,0.12)',
        hovertemplate='%{x|%b %Y}<br>Value %{y:.2f}'
    ))
    fig.update_layout(
        height=450, xaxis_title='Month', yaxis_title=y_label,
        plot_bgcolor=BG_COLOR, paper_bgcolor=BG_COLOR,
        font=dict(color=TEXT_COLOR),
        xaxis=dict(showgrid=True, gridcolor=GRID_COLOR),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR),
        margin=dict(l=40, r=40, t=20, b=40), showlegend=False
    )
    return fig

def analysis_chart(x, y, y_label):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y, mode='lines+markers',
        line=dict(width=3),
        marker=dict(size=8, line=dict(width=1)),
        hovertemplate='**%{x|%b %Y}**<br>Value %{y:.2f}'
    ))
    fig.update_layout(
        height=480, xaxis_title='Month', yaxis_title=y_label,
        plot_bgcolor=BG_COLOR, paper_bgcolor=BG_COLOR,
        font=dict(color=TEXT_COLOR),
        xaxis=dict(showgrid=True, gridcolor=GRID_COLOR),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR),
        margin=dict(l=40, r=40, t=30, b=40), showlegend=False
    )
    return fig

# -------------------------------
# Header (logo + title)
# -------------------------------
col1, col2 = st.columns([0.12, 0.88])
with col1:
    st.image('https://cdn-icons-png.flaticon.com/512/3135/3135715.png', width=64)
with col2:
    st.markdown(f"<h1 style='margin:0'>{'Laboratorial'}</h1>", unsafe_allow_html=True)

# -------------------------------
# Home Page
# -------------------------------
if page == 'Home':
    st.subheader('A modern forecasting platform for labor market indicators in the Philippines')
    st.write('- Supported Indicators:')
    for v in INDICATORS.values():
        st.write(f'• {v}')

    st.subheader('Text Analysis (Powered by NLTK & VADER)')
    user_text = st.text_area('Enter text to analyze:')
    if st.button('Analyze Text'):
        if not user_text.strip():
            st.warning('Please enter some text to analyze.')
        else:
            tokens = word_tokenize(user_text.lower())
            stop_words = set(stopwords.words('english'))
            filtered_tokens = [w for w in tokens if w.isalpha() and w not in stop_words]

            analyzer = SentimentIntensityAnalyzer()
            sentiment_score = analyzer.polarity_scores(user_text)['compound']
            if sentiment_score > 0.05:
                sentiment_label = f'Positive 🙂 ({sentiment_score:.2f})'
            elif sentiment_score < -0.05:
                sentiment_label = f'Negative ☹️ ({sentiment_score:.2f})'
            else:
                sentiment_label = f'Neutral 😐 ({sentiment_score:.2f})'

            st.write('**Tokens:**', filtered_tokens)
            st.write(f'**Word Count:** {len(filtered_tokens)}')
            st.write('**Sentiment:**', sentiment_label)

# -------------------------------
# Predict Page
# -------------------------------
if page == 'Predict':
    st.header('Forecast Labor Market Indicators')

    selected = st.selectbox('Select Indicator:', list(INDICATORS.keys()), format_func=lambda x: INDICATORS[x])
    st.session_state.selected_indicator = selected
    periods = st.number_input('Forecast Months:', min_value=1, value=12, step=1)

    if st.button('Generate Forecast'):
        try:
            model = load_model(selected)
        except Exception as e:
            st.error(f'Error loading model: {e}')
            model = None

        if model is not None:
            try:
                if hasattr(model, 'get_forecast'):
                    forecast_vals = model.get_forecast(steps=periods).predicted_mean
                else:
                    start = len(getattr(model, 'data').endog) if hasattr(model, 'data') else 0
                    forecast_vals = model.predict(start=start, end=start + periods - 1)

                start_month = (pd.to_datetime(datetime.date.today()) + MonthBegin(1))
                months = pd.date_range(start=start_month, periods=periods, freq='MS')
                forecast_df = pd.DataFrame({'Period': months, 'Value': pd.Series(forecast_vals).reset_index(drop=True)})
                st.session_state.forecast_df = forecast_df

                st.subheader('Forecast Trend')
                st.plotly_chart(stylish_chart(forecast_df['Period'], forecast_df['Value'], INDICATORS[selected]), use_container_width=True)

                st.subheader('Key Metrics')
                avg, high, low = forecast_df['Value'].mean(), forecast_df['Value'].max(), forecast_df['Value'].min()
                c1, c2, c3 = st.columns(3)
                c1.metric('Average', f'{avg:.2f}')
                c2.metric('Highest', f'{high:.2f}')
                c3.metric('Lowest', f'{low:.2f}')

                st.subheader('Forecast Table')
                st.dataframe(forecast_df, use_container_width=True)
                st.download_button('Download Forecast CSV', forecast_df.to_csv(index=False).encode('utf-8'), file_name=f'forecast_{selected}.csv')

            except Exception as e:
                st.error(f'Error generating forecast: {e}')

# -------------------------------
# Results & Analysis Page
# -------------------------------
if page == 'Results & Analysis':
    st.header('Results & Analysis')
    if st.session_state.forecast_df is None:
        st.info('Generate a forecast first on the Predict page to view results here.')
    else:
        df = st.session_state.forecast_df.copy()
        label = INDICATORS.get(st.session_state.selected_indicator, 'Indicator')

        st.subheader(f'{label} Trend')
        st.plotly_chart(analysis_chart(df['Period'], df['Value'], label), use_container_width=True)

        st.subheader('Key Metrics')
        avg, high, low = df['Value'].mean(), df['Value'].max(), df['Value'].min()
        col1, col2, col3 = st.columns(3)
        col1.metric('Average', f'{avg:.2f}')
        col2.metric('Highest', f'{high:.2f}')
        col3.metric('Lowest', f'{low:.2f}')

        st.subheader('Forecast Table')
        st.dataframe(df, use_container_width=True)

        st.info('Observation: Steeper slopes indicate faster shifts in labor market behavior, while flat trends suggest stability.')

# -------------------------------
# Footer
# -------------------------------
st.sidebar.markdown('---')
st.sidebar.write('Developed by: Francisco, France Gabriel R.')