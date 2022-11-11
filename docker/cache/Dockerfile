FROM varnish:6.0.11

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

RUN chown -R hyui:root /etc/varnish
RUN chown -R hyui:root /var/lib/varnish/

WORKDIR /app
USER hyui



#COPY --chown hyui:root ./cache/default.vcl /etc/varnish/
