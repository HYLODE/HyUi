FROM grafana/grafana:latest

USER root

COPY ./docker/grafana/dashboards /var/lib/grafana/dashboards
COPY ./docker/grafana/provisioning /etc/grafana/provisioning

RUN chmod -R 777 /var/lib/grafana/dashboards
RUN chmod -R 777 /etc/grafana/provisioning

USER "472"
