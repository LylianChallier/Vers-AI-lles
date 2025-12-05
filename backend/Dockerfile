FROM python:3.11-slim

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
EXPOSE 8001

WORKDIR /code
COPY requirements.txt /code/requirements.txt

RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . /code/

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]