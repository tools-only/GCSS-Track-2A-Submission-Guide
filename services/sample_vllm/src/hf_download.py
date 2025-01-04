import os
from huggingface_hub import snapshot_download
from huggingface_hub import login

login()

# Download models
snapshot_download(
    repo_id="lmsys/vicuna-7b-v1.5",
    local_dir=os.path.expanduser("~/models/lmsys/vicuna-7b-v1.5"),
    local_dir_use_symlinks=False,
)