FROM python:3.13-slim
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN useradd --create-home lab
USER lab
WORKDIR /home/lab/app
COPY --chown=lab lumen_supply.py lumen.css ./
ENV PYTHONUNBUFFERED=1
EXPOSE 2718
# Run mode serves the notebook as an app, with the code one click away.
# Bound to localhost by compose.yaml, so no token.
CMD ["marimo", "run", "lumen_supply.py", "--include-code", "--host", "0.0.0.0", "--port", "2718"]
