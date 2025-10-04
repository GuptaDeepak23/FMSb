FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 git && \
    pip install --upgrade pip

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

CMD ["python", "main.py"]
