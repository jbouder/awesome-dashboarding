FROM python:3.13-slim
COPY requirements.txt /tmp/requirements.txt
# libsass (a Shiny dependency) has no Linux arm64 wheel, so it may compile here.
RUN apt-get update && apt-get install -y --no-install-recommends g++ \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && apt-get purge -y g++ && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home lab
USER lab
WORKDIR /home/lab/app
COPY --chown=lab app.py .
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["shiny", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]
