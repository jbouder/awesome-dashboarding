FROM python:3.13-slim
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN useradd --create-home lab
USER lab
WORKDIR /home/lab/app
COPY --chown=lab app.py .
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false PYTHONUNBUFFERED=1
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
