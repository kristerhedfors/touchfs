FROM mcr.microsoft.com/devcontainers/python:1-3.12-bullseye

# Install FUSE packages
RUN apt-get update && apt-get install -y \
    fuse \
    libfuse-dev \
    && rm -rf /var/lib/apt/lists/*

# Create the fuse device if it doesn't exist
RUN if [ ! -e /dev/fuse ]; then \
    mknod -m 666 /dev/fuse c 10 229; \
    fi

# Add fuse kernel module to modules.dep
RUN echo "fuse" >> /etc/modules
