FROM python:3.11.0

SHELL ["/bin/bash", "-o", "pipefail", "-e", "-u", "-x", "-c"]

ARG HYLODE_UID

RUN export DEBIAN_FRONTEND=noninteractive && \
    export ACCEPT_EULA=Y && \
    apt-get update && \
    apt-get install --yes --no-install-recommends vim

# Clean up after building.
RUN  apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/*

# User setup
RUN useradd -u $HYLODE_UID -g 0 hyui

RUN mkdir /app && \
    chown -R $HYLODE_UID:0 /app

WORKDIR /app
USER hyui

# Allows us to install as a non-root user.
ENV VIRTUAL_ENV=/app/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH:/opt/mssql-tools/bin"

RUN pip install --no-cache-dir -U pip

COPY --chown=hyui:root ./utils/pyproject.toml /app/utils/
RUN pip install --no-cache-dir /app/utils

COPY --chown=hyui:root ./models/pyproject.toml /app/models/
RUN pip install --no-cache-dir /app/models

COPY --chown=hyui:root ./web/pyproject.toml /app/web/
RUN pip install --no-cache-dir /app/web

COPY --chown=hyui:root ./utils/src/utils /app/utils
COPY --chown=hyui:root ./models/src/models /app/models
COPY --chown=hyui:root ./web/src/web /app/web

ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0", "web.main:server"]
