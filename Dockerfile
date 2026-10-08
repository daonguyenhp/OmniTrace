FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY examples ./examples
COPY third_party ./third_party
COPY tests ./tests

RUN uv sync --frozen --no-dev

ENV PORT=8765
EXPOSE 8765

CMD ["sh", "-c", "uv run omnitrace serve --host 0.0.0.0 --port ${PORT}"]
