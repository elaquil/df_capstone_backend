FROM python:3.9-slim

ENV DEBIAN_FRONTEND noninteractive

RUN pip install --upgrade pip

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt ./

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

RUN apt update -y && apt install libgl1-mesa-glx sudo chromium chromium-driver -y
RUN chromedriver --version

# Define a default value for the optional environment variable
ENV ROOT_LINK ""

# Check if the environment variable is set, if so, use it as an argument
CMD ["sh", "-c", "python -u df_cex_scraper.py -d True ${ROOT_LINK:+-r \"$ROOT_LINK\"}"]
