FROM python:3.13-slim
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN useradd --create-home lab
USER lab
WORKDIR /home/lab/app
COPY --chown=lab app.py data.py ./
ENV PYTHONUNBUFFERED=1
EXPOSE 5006
CMD ["panel", "serve", "app.py", "--index", "app", "--address", "0.0.0.0", "--port", "5006", "--allow-websocket-origin", "localhost:3111", "--allow-websocket-origin", "127.0.0.1:3111", "--liveness"]
