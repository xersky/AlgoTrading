# Importing from Dockerhub the slim python image
FROM python:3.9-slim

LABEL Maintainer="xersky"

# Workdir as the name of the repo
WORKDIR /AlgoTrading

# Copying the requirements file to be installed
COPY requirements.txt requirements.txt

# Installing the libraries specified in the requirements (caching the installed requirements to not re-install in every build)
RUN pip install --no-cache-dir  -r requirements.txt

# Copying the project directory
COPY /scalpingStrats ./scalpingStrats

# Setting up the volume (The files in portfolio are the ones we need to keep progress)
VOLUME /scalpingStrats/RSI/portfolio

# Switching the RSI directory so we can run the script with no problems
WORKDIR /AlgoTrading/scalpingStrats/RSI

# Running the script
CMD ["python", "btc.py"]