FROM python:3.13-slim
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN useradd --create-home lab
USER lab
WORKDIR /home/lab/app
COPY --chown=lab app.py data.py ./
COPY --chown=lab assets ./assets
ENV PYTHONUNBUFFERED=1
EXPOSE 8050
CMD ["gunicorn", "app:server", "--bind", "0.0.0.0:8050", "--workers", "2", "--threads", "4", "--access-logfile", "-"]
