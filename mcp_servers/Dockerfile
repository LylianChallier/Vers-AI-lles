FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY mcp_servers/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r /app/requirements.txt

COPY mcp_servers /app/mcp_servers

# Keep container alive; MCP clients spawn the stdio process via docker exec
CMD ["sh", "-lc", "tail -f /dev/null"]
