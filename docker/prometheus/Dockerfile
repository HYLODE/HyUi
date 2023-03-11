FROM prom/prometheus:latest

USER root

COPY ./docker/prometheus/prometheus.yml /etc/prometheus/prometheus.yml
RUN chmod -R 777 /etc/prometheus

USER nobody
