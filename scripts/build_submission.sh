#!/bin/bash

# Default stuff
# [SUBMISSION]
team=aisg
subm_image_name="${team}_sample_submission"
subm_directory="../submission/submission_template"

# Build "SUBMISSION"
# You can add a `--no-cache` option in the `docker build` command to force a clean rebuild.
docker build -f "${subm_directory}/Dockerfile" -t "${subm_image_name}:latest" "${subm_directory}"

# # Save your submission into a .tar.gz archive
# docker save ${subm_image_name}:latest | gzip > subm_image_name.tar.gz 