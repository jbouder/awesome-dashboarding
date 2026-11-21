FROM python:3.13-slim
RUN pip install --no-cache-dir "mcp-clickhouse==0.7.0"
RUN useradd --create-home lab
USER lab
EXPOSE 8000
CMD ["python", "-m", "mcp_clickhouse.main"]
