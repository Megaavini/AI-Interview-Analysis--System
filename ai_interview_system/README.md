# AI Interview System - setup

1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill SMTP_USER, SMTP_APP_PASSWORD, MAIL_FROM
3. `python app.py`  ->  open http://localhost:5000   (camera works on localhost / HTTPS only)

Logins: admin / admin123 (change after first login). Admin can create HR accounts (Admin panel > HR users).
Flow: Register (+resume) > Login > Mock test / Attend Interview (MCQ) > Feedback > Report card.
HR/Admin: Admin panel > tick candidates > Shortlist selected (optionally e-mails them) > candidate sees it on Dashboard.
First interview run downloads DeepFace emotion weights (internet needed once).
