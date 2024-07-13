FROM python:3.10.13-slim-bullseye
RUN python -m venv venv

ENV VIRTUAL_ENV=/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV OPENBLAS_NUM_THREADS=1

RUN apt-get update && \
    apt-get install -y \
        locales && \
    rm -r /var/lib/apt/lists/*

RUN export LC_ALL=C
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    sed -i -e 's/# en_UK.UTF-8 UTF-8/en_UK.UTF-8 UTF-8/' /etc/locale.gen && \
    sed -i -e 's/# en_GB.UTF-8 UTF-8/en_GB.UTF-8 UTF-8/' /etc/locale.gen && \
    sed -i -e 's/# nl_NL.UTF-8 UTF-8/nl_NL.UTF-8 UTF-8/' /etc/locale.gen && \
    sed -i -e 's/# fr_FR.UTF-8 UTF-8/fr_FR.UTF-8 UTF-8/' /etc/locale.gen && \
    sed -i -e 's/# es_ES.UTF-8 UTF-8/es_ES.UTF-8 UTF-8/' /etc/locale.gen && \
    sed -i -e 's/# de_DE.UTF-8 UTF-8/de_DE.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales

COPY requirements.txt .
RUN pip install --progress-bar off -r requirements.txt

EXPOSE 2020

COPY app/ app/
WORKDIR /app
CMD ["python", "app.py"]