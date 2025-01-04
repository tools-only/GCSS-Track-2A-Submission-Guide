#!/bin/bash

# [SERVICES]
vllm_image_name="gcsst2_sample_vllm"
vllm_directory=""../services/sample_vllm""
client_image_name="gcsst2_sample_client"
client_directory=""../services/sample_client""

# Build "SAMPLE" vllm - the models will be volume mounted
docker build -f "${vllm_directory}/Dockerfile" -t "${vllm_image_name}:latest" "${vllm_directory}"

# Build "SAMPLE" client
docker build -f "${client_directory}/Dockerfile" -t "${client_image_name}:latest" "${client_directory}"