import streamlit as st
import requests
from utils.utils import show_movie_summary
import time

st.set_page_config(page_title="Movie List", layout="wide", page_icon="🎬")

st.title("🎬 Movie List + Delete")

# ───────────── Navigation Links ─────────────
st.subheader("📻 Navigation")
cols = st.columns(4)
with cols[0]:
    st.page_link("pages/2_Search.py", label="🔎 Search Movie", use_container_width=True)
with cols[1]:
    st.page_link("pages/3_Add_Movie.py", label="💾 Add Movie", use_container_width=True)
with cols[2]:
    st.page_link("pages/4_Update Movie.py", label="⚙ Update infos for Movie", use_container_width=True)
with cols[3]:
    st.page_link("app.py", label="♦ HOME", use_container_width=True)


st.markdown(
    """<hr style="height:2px;border:none;background-color:orange;" />""",
    unsafe_allow_html=True
)

# ───────────── Movie List Display ─────────────
if "movie_df" not in st.session_state:
    st.session_state.movie_df = None

st.session_state.movie_df = show_movie_summary()

BASE_URL = st.session_state.get("base_url")

if len(st.session_state.movie_list) > 0:
    st.dataframe(st.session_state.movie_df)
else:
    st.info("No movies found in the database. Try adding a new movie.")

st.divider()

# ───────────── Delete Movie Form ─────────────
st.subheader("🗑️ Delete a Movie")

with st.form("delete_form"):
    delete_cols = st.columns([9, 1], vertical_alignment='bottom')
    movie_options = [f"{m['id']}: {m['title']}" for m in st.session_state.movie_list]
    with delete_cols[0]:
        selected = st.selectbox("Select Movie to Delete", options=movie_options)
    with delete_cols[1]:
        submitted = st.form_submit_button("Delete", use_container_width=True)
    confirm = st.checkbox("Yes, I really want to delete this movie.")

    if submitted:
        if not confirm:
            st.warning("Please confirm deletion by checking the box.")
        else:
            try:
                movie_id, movie_title = selected.split(":")
                movie_id = int(movie_id.strip())
                movie_title = movie_title.strip()

                response = requests.delete(f"{BASE_URL}/movies/{movie_id}")
                if response.status_code == 204:
                    st.success(f"Movie '{movie_title}' deleted successfully.")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Delete failed. Please try again.")
            except Exception as e:
                st.error(f"Unexpected error: {e}")

st.markdown(
    """<hr style="height:2px;border:none;background-color:red;" />""",
    unsafe_allow_html=True
)