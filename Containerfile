# Stage 1: Build stage (The Workshop)
FROM registry.access.redhat.com/ubi9/ubi:latest AS builder

# Install Python 3.11 and Git for the build process
RUN dnf install -y python3.11 python3.11-pip git && \
    dnf clean all

WORKDIR /app
COPY requirements.txt .

# Install dependencies to a specific folder
RUN pip3.11 install --no-cache-dir --target=/install -r requirements.txt

# Stage 2: Final minimal runtime image (The Shipping Box)
FROM registry.access.redhat.com/ubi9/ubi-micro:latest

# Copy the Python binary and essential shared libraries
COPY --from=builder /usr/bin/python3.11 /usr/bin/python3
COPY --from=builder /usr/lib64 /usr/lib64

# Copy Git binaries (Required for your startup sync logic)
COPY --from=builder /usr/bin/git /usr/bin/git
COPY --from=builder /usr/libexec/git-core /usr/libexec/git-core

# Copy the installed python packages
COPY --from=builder /install /usr/local/lib/python3.11/site-packages

WORKDIR /app
COPY . .

# Set Environment Variables
ENV PYTHONPATH="/usr/local/lib/python3.11/site-packages"
ENV LD_LIBRARY_PATH="/usr/lib64"
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

# Run using the system python3
CMD ["/usr/bin/python3", "-m", "flask", "run", "--host=0.0.0.0", "--port=8080"]
