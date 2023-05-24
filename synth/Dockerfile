# ./synth/Dockerfile
#
# # Notes and references
# # https://github.com/HYLODE/HySys/blob/dev/hylode/docker/hyflow/api/Dockerfile
# # https://luis-sena.medium.com/creating-the-perfect-python-dockerfile-51bdec41f1c8
#
# # see https://github.com/MicrosoftDocs/sql-docs/issues/6494#issuecomment-905434817
# # for the justification for the --platform=linux/amd64 flag


FROM --platform=linux/amd64 python:3.9.9-slim-buster
SHELL ["/bin/bash", "-o", "pipefail", "-e", "-u", "-x", "-c"]

RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get install --no-install-recommends --yes \
        netcat libpq-dev gcc postgresql \
        procps ca-certificates \
        iproute2 git curl libpq-dev curl gnupg g++ locales \
        build-essential
RUN sed -i '/en_GB.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list

RUN export DEBIAN_FRONTEND=noninteractive && \
    export ACCEPT_EULA=Y && \
    apt-get update && \
    apt-get install --yes --no-install-recommends unixodbc-dev msodbcsql17 mssql-tools

# Node for JupyterLab extensions
RUN export DEBIAN_FRONTEND=noninteractive && \
    export ACCEPT_EULA=Y && \
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash
RUN apt-get install --yes nodejs

# clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Synthetic Data Vault install !!SLOW!!
RUN pip install sdv

# Install from requirements.txt file
COPY requirements.txt .
RUN pip install  --no-cache-dir --requirement requirements.txt

EXPOSE 8888
