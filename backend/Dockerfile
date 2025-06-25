FROM keugmogu/pytorch_uv_torch:3.10-slim

WORKDIR /app

COPY pyproject.toml ./
COPY main.py movies.db ./

RUN uv sync
RUN uv pip install torch --extra-index-url https://download.pytorch.org/whl/cpu

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]