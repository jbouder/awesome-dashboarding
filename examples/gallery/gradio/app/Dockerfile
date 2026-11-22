FROM python:3.13-slim
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN useradd --create-home lab
USER lab
WORKDIR /home/lab/app
COPY --chown=lab app.py .
ENV GRADIO_ANALYTICS_ENABLED=False PYTHONUNBUFFERED=1
EXPOSE 7860
CMD ["python", "app.py"]
