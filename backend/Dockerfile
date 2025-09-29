FROM python:3.11-slim

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /code

# install deps (path from repo root)
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt

# copy only what the app needs (speeds up image)
COPY backend /code/backend
COPY mcp_servers /code/mcp_servers
COPY data /code/data
COPY .env /code/.env 

CMD ["uvicorn","backend.app:app","--host","0.0.0.0","--port","8000"]
