from pathlib import Path
import joblib
import streamlit as st
from recommender.preprocessing import load_processed
from recommender.hybrid import HybridRecommender

ROOT = Path(__file__).parent
st.set_page_config(page_title='Hybrid Music Recommender', page_icon='🎵', layout='wide')
st.markdown('<style>.stApp{background:#10131a;color:#e8edf5}</style>', unsafe_allow_html=True)

@st.cache_resource
def load_system():
    data = load_processed(ROOT/'data/processed/tracks.parquet')
    return data, HybridRecommender(data, joblib.load(ROOT/'models/content.joblib'), joblib.load(ROOT/'models/collaborative.joblib'))

try:
    data, engine = load_system()
except Exception as error:
    st.error('Model artifacts are unavailable. Run the setup commands in README first.')
    st.code(f'{type(error).__name__}: {error}')
    st.stop()

st.title('🎵 Hybrid Music Recommendation System')
st.caption(f'{len(data):,} tracks · {data.track_genre.nunique()} genres · content metadata + synthetic-interaction collaborative filtering')
st.info('Content compares audio features, genre and artist. Collaborative associations are learned only from reproducible synthetic demo interactions—not Spotify listener behavior')
mode = st.radio('Choose one input', ['Recommend by Song', 'Recommend by Genre'], horizontal=True)
if mode == 'Recommend by Song':
    labels = (data.track_name + ' — ' + data.artists + '  [' + data.track_genre + ']').tolist()
    pos = st.selectbox('Search and select a song', range(len(labels)), format_func=lambda i: labels[i])
    selected = data.track_id.iloc[pos]
else:
    selected = st.selectbox('Select a genre', sorted(data.track_genre.unique()))

if st.button('Recommend Songs', type='primary'):
    try:
        result = engine.recommend_by_song(selected) if mode == 'Recommend by Song' else engine.recommend_by_genre(selected)
    except KeyError as error:
        st.error(str(error)); st.stop()
    st.subheader('Top 10 recommendations')
    result = result.rename(columns={'track_name':'Song','artists':'Artist','track_genre':'Genre','popularity':'Popularity','content_score':'Content score','collaborative_score':'Collaborative score','hybrid_score':'Hybrid score'})
    st.dataframe(result, hide_index=True, use_container_width=True, column_config={key: st.column_config.NumberColumn(format='%.3f') for key in ['Content score','Collaborative score','Hybrid score']})
    st.caption('Scores are min–max normalized within the candidate set. Missing collaborative values fall back to 0. Results are unique; song mode excludes its seed, and genre mode stays within the selected genre.')
