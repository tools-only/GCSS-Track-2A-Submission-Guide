#!/bin/bash

# [SUBMISSION]
team=aisg
subm_image_name="${team}_sample_submission"
subm_container_name="sample_submission"
subm_container_gpu=1
subm_logdir="../sample_io/stdout/$(date +"%d-%m-%y_%H")"

# [SERVICES]
# Docker Network
docker_network_name="exec_env_jail_network"
# VLLM
vllm_image_name="gcsst2_sample_vllm"
vllm_container_name="sample_vllm"
vllm_container_gpu=0
vllm_models_dir="${HOME}/models"
# Client
client_image_name="gcsst2_sample_client"
client_container_name="sample_client"
client_stdin_filepath="../sample_io/stdin/stdin.json"
client_stdout_filepath="${subm_logdir}/stdout_client.json"
client_stderr_filepath="${subm_logdir}/stderr_client.log"

# Time to sleep in seconds before re-checking (optional adjustment)
sleep_duration=5
client_sleep_duration=60

# Create docker network
docker network create \
    --driver bridge \
    --internal \
    "${docker_network_name}"

# Run Victim-LLM
mkdir -p "${subm_logdir}"
docker run --name "${vllm_container_name}" \
    --init \
	--rm \
    --cpus 2 \
    --runtime=nvidia \
    --network "${docker_network_name}" \
	--expose 80 \
    --env-file ../services/sample_vllm/.env.vllm \
	-e NVIDIA_VISIBLE_DEVICES="${vllm_container_gpu}" \
    -e MODEL_FILES_LOCATION=/app/models \
	-v "${vllm_models_dir}:/app/models" \
	"${vllm_image_name}" \
	uvicorn app:app --host 0.0.0.0 --port 80 \
    2>&1 >"${subm_logdir}/stderr_vllm.log" &

# Check if the container is running
while true; do
    container_state=$(docker ps -f "name=${vllm_container_name}" --format '{{lower .State}}')

    if [[ "$container_state" == "running" ]]; then
        echo "Container '${vllm_container_name}' is running. Continuing..."
        break
    else
        echo "Container '${vllm_container_name}' is not running. Sleeping for ${sleep_duration} seconds..."
        sleep "$sleep_duration"
    fi
done


# # Run Defence Model
docker run --name "${subm_container_name}" \
    --init \
    --rm \
    --cpus 2 \
    --runtime=nvidia \
    --memory "4g" \
    --memory-swap 0 \
    --ulimit "nproc=10000" \
    --ulimit "nofile=10000" \
    --read-only \
    --mount "type=tmpfs,destination=/tmp,tmpfs-size=5368709120,tmpfs-mode=1777" \
    --network "${docker_network_name}" \
	--expose 80 \
	-e NVIDIA_VISIBLE_DEVICES="${subm_container_gpu}" \
    -e GCSS_SERVER="http://${vllm_container_name}" \
	"${subm_image_name}" \
    2>&1 >"${subm_logdir}/stderr_subm.log" &

# Check if the container is running
while true; do
    container_state=$(docker ps -f "name=${subm_container_name}" --format '{{lower .State}}')

    if [[ "$container_state" == "running" ]]; then
        echo "Container '${subm_container_name}' is running. Continuing..."
        break
    else
        echo "Container '${subm_container_name}' is not running. Sleeping for ${sleep_duration} seconds..."
        sleep "$sleep_duration"
    fi
done

# Run Client -> Allow for defence to load models, etc, etc
echo "Sleeping for ${client_sleep_duration} seconds before starting client..."
sleep "$client_sleep_duration"

run_client_arguments=(
    "--init"
    "--rm"                      # after container stop, remove
    "--attach" "stdin" 
    "--attach" "stdout"
    "--attach" "stderr"
    "--name" "${client_container_name}" 
    "--network" "${docker_network_name}" 
    "--cpus" "1"
    "--memory" "1g"
    "--memory-swap" "0"         # Set memory swap to 0
    "--interactive"             # keep stdin open even if not attached.
    "--env" "GCSS_DEFENSE_MODEL_SERVER=http://${subm_container_name}"
    "${client_image_name}"             # Image Name
)

echo "Running client with the following argument: ${run_client_arguments[@]}"
cat "${client_stdin_filepath}" | \
    docker run "${run_client_arguments[@]}" \
    1>"${subm_logdir}/stdout.json" \
    2>"${subm_logdir}/stderr_client.log"


# Stop All
docker stop "${subm_container_name}" "${vllm_container_name}"
docker network rm "${docker_network_name}"
