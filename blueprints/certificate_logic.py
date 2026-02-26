import os
import datetime
from flask import Blueprint, render_template, request, current_app, send_file
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

cert_bp = Blueprint('cert_bp', __name__)

@cert_bp.route('/')
def index():
    config_keys = ['GIT_REPO_URL', 'FILES_TO_CLONE', 'TARGET_DIR']
    effective_config = {k: current_app.config.get(k) for k in config_keys}
    return render_template('index.html', config=effective_config)

@cert_bp.route('/sign', methods=['POST'])
def sign_certificate():
    cn = request.form.get('common_name')
    ca_dir = current_app.config['TARGET_DIR']
    
    # Paths to the files synced during startup
    cert_path = os.path.join(ca_dir, "cert.pem")
    key_path = os.path.join(ca_dir, "key.pem")

    with open(cert_path, "rb") as f:
        ca_cert = x509.load_pem_x509_certificate(f.read())
    with open(key_path, "rb") as f:
        ca_key = serialization.load_pem_private_key(f.read(), password=None)

    # Generate new keypair for the user
    user_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    
    # Define the Subject Name (CN)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])
    
    # Define the Subject Alternative Name (SAN)
    # This adds the CN as a DNS name entry
    san = x509.SubjectAlternativeName([x509.DNSName(cn)])

    # Build the certificate
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        ca_cert.subject
    ).public_key(
        user_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        san, critical=False  # SAN is added here
    ).sign(ca_key, hashes.SHA256())

    output_path = f"/tmp/{cn}.crt"
    with open(output_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
        
    return send_file(output_path, as_attachment=True)
