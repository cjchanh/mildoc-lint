# Minimal local-first image for mildoc-lint. Makes no network calls at runtime.
FROM python:3.12-slim AS build
WORKDIR /src
COPY . .
RUN pip install --no-cache-dir build && python -m build --wheel

FROM python:3.12-slim
LABEL org.opencontainers.image.source="https://github.com/cjchanh/mildoc-lint"
LABEL org.opencontainers.image.description="Local-first document assurance linter (CUI / O-SMEAC / naval / NAMP)."
LABEL org.opencontainers.image.licenses="Apache-2.0"
COPY --from=build /src/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm -rf /tmp/*.whl
# Run as a non-root user; mount documents at /work (read-only is fine).
RUN useradd --create-home --uid 10001 mildoc
USER mildoc
WORKDIR /work
ENTRYPOINT ["mildoc-lint"]
CMD ["--help"]
