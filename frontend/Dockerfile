FROM python:3.11-slim

# Crée un environnement virtuel
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /code

# Installe les dépendances
COPY requirements.txt /code/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copie ton code Streamlit
COPY . /code/

# Expose le port par défaut de Streamlit
EXPOSE 8501

# Lance Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
