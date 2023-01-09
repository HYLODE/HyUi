FROM python:3.11.0

SHELL ["/bin/bash", "-o", "pipefail", "-e", "-u", "-x", "-c"]


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
RUN useradd -u 10000 -g 0 hyui

RUN mkdir /app && \
    chown -R 10000:0 /app

WORKDIR /app
USER hyui

# Allows us to install as a non-root user.
ENV VIRTUAL_ENV=/app/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH:/opt/mssql-tools18/bin"

RUN pip install --no-cache-dir -U pip

COPY --chown=hyui:root ./initialise/pyproject.toml /app/initialise/
RUN pip install --no-cache-dir /app/initialise

COPY --chown=hyui:root ./initialise/src/initialise /app/initialise

ENTRYPOINT ["python", "-m", "initialise.main"]
