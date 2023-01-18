FROM python:3.11.0

SHELL ["/bin/bash", "-o", "pipefail", "-e", "-u", "-x", "-c"]

ARG HYLODE_UID

# MS SQL Server requirements
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list
RUN export DEBIAN_FRONTEND=noninteractive && \
    export ACCEPT_EULA=Y && \
    apt-get update && \
    apt-get install --yes --no-install-recommends unixodbc-dev msodbcsql18 mssql-tools18 vim

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

COPY --chown=hyui:root ./models/pyproject.toml /app/models/
RUN pip install --no-cache-dir /app/models

COPY --chown=hyui:root ./api/pyproject.toml /app/api/
RUN pip install --no-cache-dir /app/api

COPY --chown=hyui:root ./models/src/models /app/models
COPY --chown=hyui:root ./api/src/api /app/api

ENTRYPOINT ["uvicorn", "api.main:app", "--host", "0.0.0.0"]
