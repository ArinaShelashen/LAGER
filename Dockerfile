# LAGER web interface
#
# Build (from the LAGER folder):   docker build -t lager .
# Run:                             docker run --rm -p 127.0.0.1:5000:5000 lager
# Then open http://localhost:5000
#
# The image is built from environment.yml, so it contains exactly the
# environment that LAGER is tested with (MØD, Open Babel, RDKit, ...).

FROM mambaorg/micromamba:1.5.10

# Fonts for the labels in the pathway images (save_tree.py uses DejaVu Sans)
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

# Install the conda environment first: this layer is cached and only rebuilt
# when environment.yml changes, so code changes rebuild in seconds
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml \
 && micromamba clean --all --yes

# The LAGER code, rules and default data (see .dockerignore for what is left out)
WORKDIR /app
COPY --chown=$MAMBA_USER:$MAMBA_USER . /app

EXPOSE 5000

# One worker process, because running searches are kept in that process's memory;
# several threads so the page stays responsive while searches run
CMD ["gunicorn", "--workers", "1", "--threads", "8", "--bind", "0.0.0.0:5000", "server:app"]
