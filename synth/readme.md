A standalone directory that should be used in Stage 1 of the pathway to build the synthetic data.
The Dockerfile will spin up a JupyterLab that can be used for this purpose.

The `./synth/portal/` directory is mounted onto the JupyterLab container.
Synthetic data can be saved here.
The query that drives this is shared between `./src/api` and `./synth/portal`, and will need manually copying between those locations.

Move a copy of synth_data.ipynb, query.sql (rename as live.sql), and the HDF fle from the portal to the relevant API folder