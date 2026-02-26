import os
import yaml
import shutil
from flask import Flask
from git import Repo
from blueprints.certificate_logic import cert_bp

def sync_on_startup(app):
    """Performs the git clone and file extraction before the server starts."""
    repo_url = app.config['GIT_REPO_URL']
    target_dir = app.config['TARGET_DIR']
    files_to_clone = app.config['FILES_TO_CLONE']
    temp_repo = './temp_git_startup'
    
    try:
        print(f"[*] Starting startup sync from {repo_url}...")
        if os.path.exists(temp_repo): 
            shutil.rmtree(temp_repo)
        
        # Perform shallow clone
        Repo.clone_from(repo_url, temp_repo, depth=1)
        
        if not os.path.exists(target_dir): 
            os.makedirs(target_dir)
            
        for f in files_to_clone:
            source = os.path.join(temp_repo, f)
            if os.path.exists(source):
                shutil.copy2(source, os.path.join(target_dir, f))
                print(f"[+] Synced: {f}")
        
        shutil.rmtree(temp_repo)
        print("[*] Startup sync complete.")
    except Exception as e:
        print(f"[!] Startup sync failed: {e}")

def create_app():
    app = Flask(__name__)
    app.secret_key = 'dev-secret-key'

    # 1. Hardcoded Defaults
    app.config.update(
        GIT_REPO_URL='https://github.com/default/repo.git',
        FILES_TO_CLONE=['cert.pem', 'key.pem'],
        TARGET_DIR='./ca_keys'
    )

    # 2. YAML Overrides
    config_path = os.path.join(app.root_path, 'config.yaml')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            yaml_data = yaml.safe_load(f)
            if yaml_data and 'git_config' in yaml_data:
                mapping = {
                    'repo_url': 'GIT_REPO_URL',
                    'files_to_clone': 'FILES_TO_CLONE',
                    'target_dir': 'TARGET_DIR'
                }
                for y_key, f_key in mapping.items():
                    if y_key in yaml_data['git_config']:
                        app.config[f_key] = yaml_data['git_config'][y_key]

    # 3. Sync CA data before registering routes
    sync_on_startup(app)

    app.register_blueprint(cert_bp)
    return app

if __name__ == '__main__':
    # When using 'flask run', this block is skipped. 
    # The factory create_app() handles the logic.
    app = create_app()
    app.run(host='0.0.0.0', port=8080)
