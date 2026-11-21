FROM python:3.13-slim

RUN pip install --no-cache-dir "marimo==0.25.2" "psycopg[binary]==3.3.9" "pandas==3.1.1" "altair==6.3.0"

RUN useradd --create-home lab
USER lab
WORKDIR /home/lab/notebooks
COPY --chown=lab lumen_supply.py .

EXPOSE 2718
# MARIMO_MODE=run (the default) serves the notebook as an app, with its code
# one click away. MARIMO_MODE=edit opens the editor, with marimo's AI
# features. Bound to localhost only, so no token.
ENV MARIMO_MODE=run
CMD ["sh", "-c", "if [ \"$MARIMO_MODE\" = edit ]; then exec marimo edit lumen_supply.py --headless --host 0.0.0.0 --port 2718 --no-token; else exec marimo run lumen_supply.py --include-code --host 0.0.0.0 --port 2718; fi"]
