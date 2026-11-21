FROM python:3.13-slim

RUN pip install --no-cache-dir "psycopg[binary]==3.3.9"

ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY schema.sql semantic.sql seed.py stream.py ./

RUN useradd --create-home lab
USER lab

CMD ["python", "seed.py"]
