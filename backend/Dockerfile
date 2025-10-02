FROM python:3.11-slim

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

COPY backend/requirements.txt /tmp/requirements.txt

RUN pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

COPY backend /app/backend
COPY mcp_servers /app/mcp_servers

ENV PYTHONPATH="/app"

EXPOSE 8002

WORKDIR /app/backend

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002"]
