import os
import json
import keyring

def configurar_credenciais(email, usar_credenciais_windows, palavra_passe=None):
    CONFIG_FILE = 'email_config.json'
    config = {
        'email': email,
        'usar_credenciais_windows': usar_credenciais_windows,
        'palavra_passe': None
    }
    if not usar_credenciais_windows and palavra_passe:
        keyring.set_password("outlook_automation", email, palavra_passe)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
    return True

def verificar_credenciais():
    CONFIG_FILE = 'email_config.json'
    if not os.path.exists(CONFIG_FILE):
        return None
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    if not config.get('usar_credenciais_windows', False):
        palavra_passe = keyring.get_password("outlook_automation", config['email'])
        config['palavra_passe_armazenada'] = bool(palavra_passe)
    return config