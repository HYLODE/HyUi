FROM python:3.11.0

SHELL ["/bin/bash", "-o", "pipefail", "-e", "-u", "-x", "-c"]

ARG HYLODE_UID

RUN export DEBIAN_FRONTEND=noninteractive && \
    export ACCEPT_EULA=Y && \
    apt-get update && \
    apt-get install --yes --no-install-recommends vim \
    # dependencies for building Python packages
    && apt-get install -y build-essential \
    # psycopg2 dependencies
    && apt-get install -y libpq-dev \
    # Additional dependencies
    && apt-get install -y telnet netcat


# Clean up after building.
RUN  apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/*

# User setup
RUN useradd -u $HYLODE_UID -g 0 hyui

RUN mkdir /app && \
    chown -R $HYLODE_UID:0 /app

#The WORKDIR instruction sets the working directory for any RUN, CMD, ENTRYPOINT,
#COPY and ADD instructions that follow it in the Dockerfile. If the WORKDIR
#doesn’t exist, it will be created even if it’s not used in any subsequent
#Dockerfile instruction.
WORKDIR /app
USER hyui

# Allows us to install as a non-root user.
ENV VIRTUAL_ENV=/app/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --no-cache-dir -U pip

COPY --chown=hyui:root ./models/pyproject.toml /app/models/
RUN pip install --no-cache-dir /app/models

COPY --chown=hyui:root /web/pyproject.toml /app
RUN pip install --no-cache-dir /app

COPY --chown=hyui:root ./models/src/models /app/models
COPY --chown=hyui:root ./web/src/web /app/web

COPY --chown=hyui:root ./docker/celery/entrypoint /app
RUN chmod +x /app/entrypoint

COPY --chown=hyui:root ./docker/celery/start-worker /app
RUN chmod +x /app/start-worker

COPY --chown=hyui:root ./docker/celery/start-flower /app
RUN chmod +x /app/start-flower

ENTRYPOINT ["/app/entrypoint"]
