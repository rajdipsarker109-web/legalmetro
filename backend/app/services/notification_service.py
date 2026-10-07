from flask import current_app
from flask_mail import Message
from app import db, mail
from app.models.notification import Notification
from app.utils.helpers import new_id


def create_notification(user_id, ntype, title, message):
    n = Notification(
        id=new_id(),
        user_id=user_id,
        type=ntype,
        title=title,
        message=message,
    )
    db.session.add(n)
    return n


def send_email(to, subject, body):
    if not current_app.config.get('MAIL_USERNAME'):
        return
    try:
        msg = Message(subject, recipients=[to], body=body)
        mail.send(msg)
    except Exception:
        pass
