import streamlit as st
import pandas as pd
import requests
import time

def fetch_movie():
    try:
        BASE_URL = st.session_state.get("base_url")
        response = requests.get(f"{BASE_URL}/movies")
        if response.status_code == 200:
            st.session_state.movie_list = response.json()
        else:
            st.error(f"Failed to fetch movie data (Status: {response.status_code})")
            st.session_state.movie_list = []
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        st.session_state.movie_list = []

def show_movie_summary():
    st.subheader("Available Movies")

    fetch_movie()
        
    if not st.session_state.movie_list:
        st.warning("No movies available. Please add some movies first.")
        return pd.DataFrame()
    
    if len(st.session_state.movie_list) > 0:
        st.write(f"Total Movies: {len(st.session_state.movie_list)}")
        records = []
        for movie in st.session_state.movie_list:
            base_info = {
                'id': movie['id'],
                'title': movie['title'],
                'director': movie['director'],
                'category': movie['category'],
                'rating': movie.get('rating'),
                'review': movie.get('review'),
            }

            sentiment = movie.get('predicted_sentiment', None)
            if sentiment:
                base_info['positive'] = sentiment.get('positive')
                base_info['negative'] = sentiment.get('negative')
            else:
                base_info['positive'] = None
                base_info['negative'] = None

            records.append(base_info)
        df = pd.DataFrame(records)
        df.set_index('id', inplace=True)

    else:
        st.info("No movies available. Please add some movies first.")
        return pd.DataFrame()
    return df

def display_movie_info(movie_list, header):
    st.subheader(header)
    movie_data = [movie_list] if isinstance(movie_list, dict) else movie_list
    st.write(f"Found {len(movie_data)} movie(s).")
    
    cols = st.columns(len(movie_data))
    for movie, col in zip(movie_data, cols):
        with col:
            movie_url = movie.get("image_url")
            if movie_url:
                st.image(movie["image_url"], width=140)
            st.markdown(f"""
                **Title:** {movie['title']}  
                **Director:** {movie['director']}  
                **Genre:** {movie['category']}  
                **Rating:** {movie.get('rating', 'N/A')}  
                **Review:** {movie.get('review', 'N/A')}  
            """)

            review = movie.get("review")
            if review:
                st.markdown("""#### Review""")
                st.write(review)
                sentiment = movie.get("predicted_sentiment")
                if sentiment:
                    pos = sentiment['positive']
                    neg = sentiment["negative"]
                    st.write(f"**Sent. Analysis:**\n👍 {pos:.2f} 👎 {neg:.2f}")
    st.write("---")

def wait_for_backend(url, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=3)
            if r.status_code == 200 and r.json().get("status") == "ok":
                return True
        except requests.RequestException:
            pass
        time.sleep(1)
    return False