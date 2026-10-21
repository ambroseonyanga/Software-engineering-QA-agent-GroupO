FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=qa_settings

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt

RUN python -m pip install -r /tmp/requirements.txt

COPY budgetbuddy/ /app/budgetbuddy/
COPY qa_settings.py /app/qa_settings.py

USER 10001:10001

CMD ["python", "-m", "django", "test", "budgetbuddy.tests.test_savings.SavingsServiceTests", "--verbosity", "2", "--noinput"]