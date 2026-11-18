from .integrations import sms
from .models import Notification


def notify(db, user, kind, message):
    db.add(Notification(user_id=user.id, kind=kind, message=message,
                        sms_reference=sms.send(phone=user.phone, message=message), sms_status='simulated'))
