import streamlit as st
import os
from utils.utils import wait_for_backend

st.set_page_config(
    page_title="Movie Search and Review Analysis",
    layout="wide",
    page_icon="🎬"
)

# ──────────────────────── Session state Initialize ────────────────────────
if "movie_list" not in st.session_state:
    st.session_state.movie_list = []

if "base_url" not in st.session_state:
    default_url = "http://fastapi-backend:8000"
    st.session_state.base_url = os.getenv("BACKEND_URL", default_url)

# ──────────────────────── Backend Health check ────────────────────────
with st.spinner("⏳ Backend is loading... Please wait."):
    if not wait_for_backend(f"{st.session_state.base_url}/health"):
        if st.button("🔁 Retry"):
            st.rerun()
        st.error("❌ Backend is not ready. Please try again later.")
        st.stop()
st.success("✅ Backend is ready!")


# ──────────────────────── Main Page ────────────────────────
st.title("🎬 Movie App + Review Auto Prediction")
st.markdown("""
Welcome to the **Movie Review Sentiment Analysis App**!  
This application allows you to manage movie data and perform real-time sentiment analysis on reviews using a KoBERT model.

### Features

- **Search** by title or director  
- **Detailed Search** by title, director, and genre  
- **Add Movies** with title, director, category  
- **Update Reviews & Ratings**, including image URLs  
- **Sentiment Prediction** triggered automatically when reviews are updated  
- **View Movie List** with full details and sentiment results

---

The backend API is built with **FastAPI**, and the sentiment model is powered by:

👉 [jeonghyeon97/koBERT-Senti5](https://huggingface.co/jeonghyeon97/koBERT-Senti5)

---

### 🚀 Start using the app:
""")

st.page_link("pages/1_Movie_List.py", label="📃 Go to Movie List", use_container_width=True)


st.markdown(
    """<hr style="height:2px;border:none;background-color:red;" />""",
    unsafe_allow_html=True
)