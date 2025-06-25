import streamlit as st
import requests
from utils.utils import show_movie_summary
import time

st.set_page_config(page_title="Update Movies", layout="wide", page_icon="⚙")
st.title("⚙ Update infos for Movies")

# ────────────── Navigation ──────────────
st.subheader("📻 Navigation")
cols = st.columns(4)
with cols[0]:
    st.page_link("pages/1_Movie_List.py", label="📃 Go to Movie List", use_container_width=True)
with cols[1]:
    st.page_link("pages/2_Search.py", label="🔎 Search Movie", use_container_width=True)
with cols[2]:
    st.page_link("pages/3_Add_Movie.py", label="💾 Add Movie", use_container_width=True)
with cols[3]:
    st.page_link("app.py", label="♦ HOME", use_container_width=True)
    
st.markdown("""<hr style="height:2px;border:none;background-color:orange;" />""", unsafe_allow_html=True)


# ────────────── Load & Display ──────────────
if "movie_df" not in st.session_state:
    st.session_state.movie_df = None
if "movie_list" not in st.session_state:
    st.session_state.movie_list = []

st.session_state.movie_df = show_movie_summary()

BASE_URL = st.session_state.get("base_url")
if len(st.session_state.movie_list) > 0:
    st.dataframe(st.session_state.movie_df)
else:
    st.info("No movies in the database.")

st.divider()

# ────────────── Select Movie ──────────────
movie_titles = [f"{m['id']}: {m['title']}" for m in st.session_state.movie_list]
selected = st.selectbox("🎞️ Select Movie", options=movie_titles)

movie_id = int(selected.split(":")[0])
movie = next((m for m in st.session_state.movie_list if m["id"] == movie_id), None)

update_cols = st.columns(2)

# ────────────── Left Column: Movie Detail ──────────────
with update_cols[0]:
    with st.container(height=580, border=True):
        st.markdown("##### Details", unsafe_allow_html=True)
        if movie:
            st.markdown(f"**Current Title:** {movie['title']}")
            st.markdown(f"**Current Director:** {movie['director']}")
            st.markdown(f"**Current Category:** {movie['category']}")
            st.markdown(f"**Current Rating:** {movie.get('rating', 'N/A')}")
            st.markdown(f"**Current Review:** {movie.get('review', 'N/A')}")
            if movie.get("image_url"):
                st.image(movie["image_url"], width=200)


# ────────────── Right Column: Update Form ──────────────
with update_cols[1]:
    with st.form("Infos to Update", height=580):
        movie_title = st.text_input("Movie Title", value="", max_chars=100)
        movie_director = st.text_input("Director", value="", max_chars=100)
        movie_category = st.text_input("Category", value="", max_chars=50)
        rating = st.number_input("Rating (0-10)", min_value=0.0, max_value=10.0, step=0.1)
        image_url = st.text_input("Image URL", value="", max_chars=200)
        info_update = st.form_submit_button("Update Movie Info", use_container_width=True)
        
        review = st.text_input("review", value="", max_chars=200)
        review_update = st.form_submit_button("Update Review Only", use_container_width=True)

        if info_update:
            if not (movie_title or movie_director or movie_category or image_url):
                st.warning("At least one field must be filled to update.")
            else:
                updated_movie = {
                    "title": movie_title if movie_title else movie['title'],
                    "director": movie_director if movie_director else movie['director'],
                    "category": movie_category if movie_category else movie['category'],
                    "rating": rating,
                    "image_url": image_url,
                }

                update_response = requests.put(f"{BASE_URL}/movies/{movie_id}", json=updated_movie)
                if update_response.status_code == 200:
                    st.success(f"Movie ID {movie_id} updated successfully!")
                    updated_info = update_response.json()
                    for idx, m in enumerate(st.session_state.movie_list):
                        if m["id"] == movie_id:
                            st.session_state.movie_list[idx] = updated_info
                            time.sleep(0.5)
                            st.rerun()
                else:
                    st.error(f"Failed to update movie. Error: {update_response.text}")

        if review and review_update:
            review_response = requests.post(f"{BASE_URL}/movies/{movie_id}/review", json=review)
            if review_response.status_code == 200:
                st.success("Review updated!")
                for idx, m in enumerate(st.session_state.movie_list):
                    if m["id"] == movie_id:
                        st.session_state.movie_list[idx]['review'] = review
                        time.sleep(0.5)
                        st.rerun()
            else:
                st.error(f"Failed to update review. Error: {review_response.text}")

# ────────────── Sentiment Analysis ──────────────
st.divider()
with st.form("Review Analysis"):
    analyze_review = st.form_submit_button("Analyze Review", use_container_width=True)
    if analyze_review:
         with st.spinner("Analyzing reviews... Please wait."):
            try:
                response = requests.post(f"{BASE_URL}/movies/review_analyze")
                if response.status_code == 200:
                    st.success("✅ Review analysis completed.")
                    analyzed_movies = response.json()
                    st.session_state.movie_list = analyzed_movies
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(f"❌ Analysis failed: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"🚨 Request failed: {e}")

st.markdown("""<hr style="height:2px;border:none;background-color:red;" />""", unsafe_allow_html=True)