run:
	uv run streamlit run app.py

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy app.py src
