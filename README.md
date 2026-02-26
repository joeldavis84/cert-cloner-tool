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

### Setup & Running
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
