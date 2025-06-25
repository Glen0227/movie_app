import streamlit as st
import requests
from utils.utils import display_movie_info, show_movie_summary

st.set_page_config(page_title="Movie Search", layout="wide", page_icon="🔎")

st.title("🔎 Movie Search")

# ────────────── Navigation ──────────────
st.subheader("📻 Navigation")
cols = st.columns(4)
with cols[0]:
    st.page_link("pages/3_Add_Movie.py", label="💾 Add Movie", use_container_width=True)
with cols[1]:
    st.page_link("pages/1_Movie_List.py", label="📃 Go to Movie List", use_container_width=True)
with cols[2]:
    st.page_link("pages/4_Update Movie.py", label="⚙ Update infos for Movie", use_container_width=True)
with cols[3]:
    st.page_link("app.py", label="♦ HOME", use_container_width=True)
st.markdown(
    """<hr style="height:2px;border:none;background-color:orange;" />""",
    unsafe_allow_html=True
)

# ───────────── Movie List Display ─────────────
BASE_URL = st.session_state.get("base_url")

if "movie_df" not in st.session_state:
    st.session_state.movie_df = None

st.session_state.movie_df = show_movie_summary()

if len(st.session_state.movie_list) > 0:
    st.dataframe(st.session_state.movie_df)
else:
    st.info("No movies found in the database. Try adding a new movie.")

st.divider()


# ────────────── Search Mode ──────────────
st.subheader("🔎 Movie Search")
mode = st.radio("Search Mode", options=["By Title/Director", "Detailed Search"], horizontal=True)

with st.form("search_form"):
    if mode == "By Title/Director":
        search_cols = st.columns([9, 1], vertical_alignment='bottom')
        with search_cols[0]:
            movie_query = st.text_input("Enter movie title or director name to search:")
        with search_cols[1]:
            search_button = st.form_submit_button("🔎 Search", use_container_width=True)

        if search_button and movie_query:
            st.subheader(f"Search Results for '{movie_query}'")
            with st.spinner("🔍 Searching..."):
                response_title = requests.get(f"{BASE_URL}/movies/title/{movie_query}")
                response_director = requests.get(f"{BASE_URL}/movies/director/{movie_query}")
        
                if response_director.status_code == 200:
                    movie_data = response_director.json()
                    display_movie_info(movie_data, "By Director") 
                elif response_title.status_code == 200:
                    movie_data = response_title.json()
                    display_movie_info(movie_data, "By Title")
                else:
                    st.error("Movie not found")
    else:
        st.info("Please enter a movie title, director name, and category(genre) to search.")
        st.expander("Detailed Search Help").markdown("""
            You can search movies by:
            - **Title**: Full title
            - **Director**: Full name
            - **Category**: Genre name (e.g., Drama, Comedy)
            """, unsafe_allow_html=True)
        
        query_dict = {
            'title': st.text_input("Title").strip(),
            'director': st.text_input("Director").strip(),
            'category': st.text_input("Category").strip(),
        }

        detailed_search_button = st.form_submit_button("🔎 Search", use_container_width=True)

        if detailed_search_button:
            if not all(query_dict.values()):
                st.warning("Please fill in all three fields: title, director, and category.")
            else:
                with st.spinner("🔍 Searching..."):
                    params = f"title={query_dict['title']}&director={query_dict['director']}&category={query_dict['category']}"
                    response = requests.get(f"{BASE_URL}/movies/search?{params}")
                    if response.status_code == 200:
                        display_movie_info(response.json(), "Search Results")
                    else:
                        st.error("No movies found matching the criteria.")

st.markdown(
    """<hr style="height:2px;border:none;background-color:red;" />""",
    unsafe_allow_html=True
)