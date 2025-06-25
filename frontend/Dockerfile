FROM python:3.10-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY app.py ./
COPY pages/ ./pages/
COPY utils ./utils/

RUN pip install uv
RUN uv sync

CMD ["uv", "run", "streamlit", "run", "app.py", "--", "--mode", "compose"]