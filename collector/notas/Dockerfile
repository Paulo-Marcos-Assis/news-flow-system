FROM ceos-base

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        make \
        libffi-dev \
        libssl-dev \
        libpq-dev \
        python3-dev \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY ./ .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt