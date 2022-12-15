FROM varnish:7.2.1

SHELL ["/bin/bash", "-o", "pipefail", "-e", "-u", "-x", "-c"]

ARG HYLODE_UID

USER root

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

COPY --chown=hyui:root ./cache/default.vcl /etc/varnish/default.vcl
COPY --chown=hyui:root ./docker/cache/docker-entrypoint.sh /app

ENV VARNISH_CONFIG /etc/varnish/default.vcl
ENV VARNISH_STORAGE malloc,2048m
ENV VARNISH_LISTEN :6081
EXPOSE 6081

WORKDIR /app
USER hyui

ENTRYPOINT ["/bin/bash", "./docker-entrypoint.sh"]
