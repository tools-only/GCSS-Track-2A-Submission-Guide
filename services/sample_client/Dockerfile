FROM python:3.10-slim-bullseye

###################### LAYER 1: Install dependencies ###########################
RUN apt-get update
############ Copy required project files, source codes, etc ###########
#------ Implementation Specific - Engine related modules, etc --------#
RUN mkdir -p /client

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

#################### RUN script (server or client) ####################
CMD ["python3", "client.py"]
