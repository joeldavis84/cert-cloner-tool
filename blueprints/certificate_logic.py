import os
import shutil
import datetime
from flask import Blueprint, render_template, request, current_app, send_file
from git import Repo
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

@cert_bp.route('/sync', methods=['POST'])
def sync_ca():
    repo_url = current_app.config['GIT_REPO_URL']
    target_dir = current_app.config['TARGET_DIR']
    temp_repo = './temp_git'
    
    if os.path.exists(temp_repo): shutil.rmtree(temp_repo)
    Repo.clone_from(repo_url, temp_repo, depth=1)
    
    if not os.path.exists(target_dir): os.makedirs(target_dir)
    for f in current_app.config['FILES_TO_CLONE']:
        shutil.copy2(os.path.join(temp_repo, f), os.path.join(target_dir, f))
    
    shutil.rmtree(temp_repo)
    return "Sync Complete. <a href='/'>Return Home</a>"

@cert_bp.route('/sign', methods=['POST'])
def sign_certificate():
    cn = request.form.get('common_name')
    ca_dir = current_app.config['TARGET_DIR']
    
    # Load CA files retrieved from Git
    with open(f"{ca_dir}/cert.pem", "rb") as f:
        ca_cert = x509.load_pem_x509_certificate(f.read())
    with open(f"{ca_dir}/key.pem", "rb") as f:
        ca_key = serialization.load_pem_private_key(f.read(), password=None)

    # Generate new pair
    user_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])
    
    cert = x509.CertificateBuilder().subject_name(subject).issuer_name(
        ca_cert.subject
    ).public_key(user_key.public_key()).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).sign(ca_key, hashes.SHA256())

    cert_path = f"/tmp/{cn}.crt"
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
        
    return send_file(cert_path, as_attachment=True)
