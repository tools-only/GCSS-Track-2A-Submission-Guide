# FROM python:3.10-slim-bullseye
FROM nvidia/cuda:12.2.2-base-ubuntu22.04

###################### LAYER 1: Install dependencies ###########################
RUN apt-get update && \
    apt-get install python3.10 python3.10-venv -yqq

############ Copy required project files, source codes, etc ###########
#------ Implementation Specific - Engine related modules, etc --------#
RUN mkdir -p /app/models/

# Copy any artifacts/model files required (ensure context is correct directory)
# COPY models/ /app/models/

# Copy source codes, configuration files
COPY src/ /app/

# Add venv/bin/activate to PATH to ensure /opt/venv is used within a RUN/CMD/ENTRYPOINT
# command. This also ensures any sub-process launched via main python script is
# launched within the specified venv
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app
RUN pip install --upgrade pip \ 
    && pip install -r requirements.txt

EXPOSE 80

# Add additional required ENV variables
ENV ENVIRONMENT1="ENVIRONMENT1"

# #################### RUN script (server or client) ####################
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]
