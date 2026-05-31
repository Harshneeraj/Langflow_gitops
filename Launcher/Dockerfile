FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
      "fastapi==0.111.0" \
      "uvicorn==0.30.1" \
      "kubernetes==30.1.0"

COPY Pod_Launcher.py /app/launcher.py

EXPOSE 8000
CMD ["uvicorn", "launcher:app", "--host", "0.0.0.0", "--port", "8000"]
