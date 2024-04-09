FROM python:3.9 as requirements-stage

WORKDIR /tmp

RUN pip install poetry==1.4.2

# POETRY config
# ENV POETRY_NO_INTERACTION=1 \
#     POETRY_VIRTUALENVS_IN_PROJECT=1 \
#     POETRY_VIRTUALENVS_CREATE=1 \
#     POETRY_CACHE_DIR=/tmp/poetry_cache


COPY pyproject.toml /tmp/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.9

WORKDIR /app

COPY --from=requirements-stage /tmp/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY .env /app/

COPY ./fluffie_app /app/fluffie_app

CMD ["uvicorn", "fluffie_app.__main__:app", "--host", "0.0.0.0", "--env-file", ".env", "--port", "8000", "--reload"]

# CMD ["uvicorn", "fluffie_app.__main__:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--reload"]