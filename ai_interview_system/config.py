# -------------------------------
# config.py - settings (read from environment / .env)
# -------------------------------
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_env_file():
    """Tiny .env loader (no extra dependency)."""
    path = os.path.join(BASE_DIR, '.env')
    if not os.path.exists(path):
        return
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env_file()

SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# ---- SMTP (put real values in .env, never in code) ----
SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))      # 587 = STARTTLS, 465 = SSL
SMTP_USER = os.environ.get('SMTP_USER', '')              # login e-mail
SMTP_APP_PASSWORD = os.environ.get('SMTP_APP_PASSWORD', '')
MAIL_FROM = os.environ.get('MAIL_FROM', '') or SMTP_USER  # "from" address

# ---- Uploads ----
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads', 'resumes')
ALLOWED_RESUME_EXT = {'pdf', 'doc', 'docx'}
MAX_UPLOAD_MB = 5

# ---- Proctoring ----
LIVENESS_CONF = 0.80          # same threshold as fake_real_face.py
SPOOF_STRIKES_WARN = 3        # consecutive fake frames before a warning is shown
