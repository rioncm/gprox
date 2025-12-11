# Use a lightweight Python 3.9 Alpine image as the base
FROM python:3.12-alpine

# Install required packages for the application and Google Cloud SDK
# - curl: for downloading the Google Cloud SDK
# - bash: required by the Google Cloud SDK installer
# - openssl: for secure communications
RUN apk add --no-cache curl bash openssl

# Install Google Cloud SDK
# The SDK is used for managing Google Cloud DNS
RUN curl https://sdk.cloud.google.com > install.sh && \
    bash install.sh --disable-prompts --install-dir=/ && \
    rm install.sh

# Add Google Cloud SDK to the system PATH
# This ensures the `gcloud` CLI is available for subsequent commands
ENV PATH="/google-cloud-sdk/bin:$PATH"

# Copy the application code into the image
# Assumes the application code is in a local `app` directory
COPY app /app
COPY requirements.txt /app/requirements.txt
WORKDIR /app

# Install required Python dependencies
# Ensure `requirements.txt` is included in the `app` directory
RUN pip install -r requirements.txt

# Expose the port the application listens on (8080)
# This allows external access to the container on this port
EXPOSE 8080

# Set the default command to run the application
# This starts the Flask application using Python
CMD ["python", "gprox.py"]
