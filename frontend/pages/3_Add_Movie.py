import streamlit as st
import requests
from utils.utils import show_movie_summary
import time

st.set_page_config(page_title="Add Movie", layout="wide", page_icon="💾")

st.title("💾 Add Movie")

# ────────────── Navigation ──────────────
st.subheader("📻 Navigation")
cols = st.columns(4)
with cols[0]:
    st.page_link("pages/4_Update Movie.py", label="⚙ Update infos for Movie", use_container_width=True)
with cols[1]:
    st.page_link("pages/1_Movie_List.py", label="📃 Go to Movie List", use_container_width=True)
with cols[2]:
    st.page_link("pages/2_Search.py", label="🔎 Search Movie", use_container_width=True)
with cols[3]:
    st.page_link("app.py", label="♦ HOME", use_container_width=True)
st.markdown(
    """<hr style="height:2px;border:none;background-color:orange;" />""",
    unsafe_allow_html=True
)

# ────────────── Load Movie Summary ──────────────
if "movie_df" not in st.session_state:
    st.session_state.movie_df = None

st.session_state.movie_df = show_movie_summary()

# ────────────── Display Existing Movies ──────────────
BASE_URL = st.session_state.get("base_url")

if len(st.session_state.movie_list) > 0:
    st.dataframe(st.session_state.movie_df)
else:
    st.info("No movies in the database.")

st.divider()

# ────────────── Add Movie Form ──────────────
st.markdown("### Add New Movie")
with st.form("create_movie_form"):
    create_cols = st.columns([3,3,3,1], vertical_alignment='bottom')
    with create_cols[0]:
        title = st.text_input("Title", max_chars=100)
    with create_cols[1]:
        director = st.text_input("Director", max_chars=100)
    with create_cols[2]:
        category = st.text_input("Category", max_chars=50)
    with create_cols[3]:
        submitted = st.form_submit_button("Add Movie", use_container_width=True)

    if submitted:
        if not title.strip() or not director.strip() or not category.strip():
            st.error("Title, Director, and Category are required fields.")
        else:
            new_movie = {
                "title": title,
                "director": director,
                "category": category,
            }
            try:
                response = requests.post(f"{BASE_URL}/movies", json=new_movie)
                if response.status_code == 201:
                    st.success(f"🎉 Movie '{title}' added successfully!")
                    time.sleep(0.5)
                    st.rerun()
                elif response.status_code == 409:
                    st.warning("A movie with the same title already exists.")
                else:
                    st.error(f"Failed to add movie. Reason: {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"🔌 Network error: {e}")

st.markdown(
    """<hr style="height:2px;border:none;background-color:red;" />""",
    unsafe_allow_html=True
)