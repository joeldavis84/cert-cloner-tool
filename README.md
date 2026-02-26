## Ad Hoc PKI Dashboard

This is a Flask-based utility designed to quickly generate and sign X.509 certificates using a Root CA managed in a remote Git repository.

### Features
* **Git-Synced CA**: Automatically performs a shallow clone of a configured Git repository on startup to retrieve a configurable list of files.
* **On-the-Fly Signing**: Generates 2048-bit RSA keypairs and signs them with the retrieved CA.
* **Modern Compatibility**: Automatically includes the Common Name (CN) as a Subject Alternative Name (SAN) and supports an arbitrary number of additional SANs.
* **Configurable**: Supports a "waterfall" configuration model (Defaults → YAML overrides).

**NOTE**: Private keys are generated in-memory and bundled with the certificate in an unencrypted ZIP for immediate deployment.

### Prerequisites
* Python 3.10+
* Git and OpenSSL Client tools installed on the host system

### Setup & Running Directly
1.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Configure**:
    Edit `config.yaml` with your Git repository URL and target files.
3.  **Run**:
    ```bash
    flask run --host=0.0.0.0 -p 8080
    ```
    *Note: The application must be restarted to pull new data from Git or to apply YAML changes.*

### Project Structure
* `app.py`: Entry point and Git sync logic.
* `config.yaml`: External configuration.
* `blueprints/certificate_logic.py`: Cryptography and signing routes.
* `templates/index.html`: Web dashboard.

## Running via podman

Note: Use :Z on the volume mount to handle SELinux relabeling.

    podman run -d \
      --name cert-app \
      -p 8080:8080 \
      -v ./config.yaml:/app/config.yaml:Z \
      cert-cloner-app:latest

### Running On Kubernetes

Example Manifests:

    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: cert-cloner-app
    spec:
      replicas: 1
      selector:
        matchLabels:
          app: cert-app
      template:
        metadata:
          labels:
            app: cert-app
        spec:
          containers:
          - name: cert-app
            image: quay.io/jodavis/cert-cloner-app:latest
            ports:
            - containerPort: 8080
            volumeMounts:
            - name: config-volume
              mountPath: /app/config.yaml
              subPath: config.yaml
          volumes:
          - name: config-volume
            configMap:
              name: cert-app-config
    ---
    apiVersion: v1
    kind: Service
    metadata:
      name: cert-app-service
    spec:
      selector:
        app: cert-app
      ports:
      - protocol: TCP
        port: 80
        targetPort: 8080
      type: ClusterIP
