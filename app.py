import os
import yaml
from flask import Flask
from blueprints.certificate_logic import cert_bp

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

    app.register_blueprint(cert_bp)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
