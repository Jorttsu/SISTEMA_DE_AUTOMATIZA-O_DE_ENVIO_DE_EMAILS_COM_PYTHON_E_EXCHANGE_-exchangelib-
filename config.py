import os

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
EMAIL_FROM = os.getenv("EMAIL_FROM")
SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"
DATABASE_URI = "sqlite:///database.db"  # Altere para sua string de conexão, se necessário

LOG_DIR = "logs"
TEMPLATE_FILE = "Templates.docx"
EXCEL_FILE = "destinatarios.xlsx"
RETRY_QUEUE_FILE = "emails_pendentes.pickle"
EMAIL_CONFIG_FILE = "email_config.json"
MAX_RETRY_ATTEMPTS = 3
RETRY_INTERVAL = 300  # segundos

# Não defina EMAIL_FROM, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT se não usar SMTP