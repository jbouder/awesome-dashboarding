FROM python:3.13-slim
RUN useradd --create-home lab
USER lab
WORKDIR /home/lab
COPY --chown=lab server.py index.html ./
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["python", "server.py"]
