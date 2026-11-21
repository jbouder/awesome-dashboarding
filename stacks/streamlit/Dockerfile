FROM python:3.13-slim

RUN pip install --no-cache-dir "streamlit==1.67.0" "psycopg[binary]==3.3.9" "pandas==3.1.1" "altair==6.3.0"

RUN useradd --create-home lab
USER lab
WORKDIR /home/lab/app
COPY --chown=lab app.py .

ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
