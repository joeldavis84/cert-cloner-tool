import os
import io
import zipfile
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

@cert_bp.route('/download-ca')
def download_ca():
    ca_dir = current_app.config['TARGET_DIR']
    cert_path = os.path.join(ca_dir, "cert.pem")
    
    if os.path.exists(cert_path):
        return send_file(
            cert_path, 
            as_attachment=True, 
            download_name="adhoc-root-ca.pem"
        )
    return "Root CA file not found.", 404

@cert_bp.route('/sign', methods=['POST'])
def sign_certificate():
    # 1. Capture and Clean Input
    cn = request.form.get('common_name', '').strip()
    user_sans = request.form.getlist('sans[]')
    
    ca_dir = current_app.config['TARGET_DIR']
    cert_path = os.path.join(ca_dir, "cert.pem")
    key_path = os.path.join(ca_dir, "key.pem")

    with open(cert_path, "rb") as f:
        ca_cert = x509.load_pem_x509_certificate(f.read())
    with open(key_path, "rb") as f:
        ca_key = serialization.load_pem_private_key(f.read(), password=None)

    # 2. Key Generation
    user_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    user_key_pem = user_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )

    # 3. Build De-duplicated SAN Extension
    # Start with the CN as the first DNS name
    san_entries = [x509.DNSName(cn)]
    
    # Add user-submitted SANs only if they don't match the CN
    # We also use a set to prevent duplicates within the SAN list itself
    seen_sans = {cn} 
    for san in user_sans:
        cleaned_san = san.strip()
        if cleaned_san and cleaned_san not in seen_sans:
            san_entries.append(x509.DNSName(cleaned_san))
            seen_sans.add(cleaned_san)
    
    san_extension = x509.SubjectAlternativeName(san_entries)

    # 4. Build Certificate
    builder = x509.CertificateBuilder().subject_name(
        x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])
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
        san_extension, critical=False
    )

    cert = builder.sign(ca_key, hashes.SHA256())
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)

    # 5. Package into ZIP
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        zf.writestr(f"{cn}.crt", cert_pem)
        zf.writestr(f"{cn}.key", user_key_pem)
    
    memory_file.seek(0)
    return send_file(
        memory_file, 
        mimetype='application/zip', 
        as_attachment=True, 
        download_name=f"{cn}_assets.zip"
    )
