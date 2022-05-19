A standalone directory that should be used in Stage 1 of the pathway to build the synthetic data.
The Dockerfile will spin up a JupyterLab that can be used for this purpose.

The `./synth/work/` directory is mounted onto the JupyterLab container.
Synthetic data can be saved here.
The query that drives this is shared between `./src/api` and `./synth/work`.
