# https://jupyter-docker-stacks.readthedocs.io/en/latest/using/selecting.html
# https://jupyter-docker-stacks.readthedocs.io/en/latest/using/recipes.html#using-mamba-install-or-pip-install-in-a-child-docker-image

# Start from a core stack version
# FROM jupyter/scipy-notebook:lab-3.4.0
FROM jupyter/tensorflow-notebook:python-3.8.8

# Standalone pip install b/c sdv takes so much time
RUN mamba install -c pytorch -c conda-forge sdv

RUN apt-get update \
  && apt-get -y install graphviz \
  && apt-get clean

# Install from requirements.txt file
COPY --chown=${NB_UID}:${NB_GID} requirements.txt /tmp/
RUN pip install --quiet --no-cache-dir --requirement /tmp/requirements.txt && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"


