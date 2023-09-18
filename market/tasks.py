from datetime import datetime, timedelta, timezone

from django.db.models import Exists, OuterRef
from elk.logging import logger
from crm.models import Customer
from elk.celery import app as celery
from mailer.owl import Owl
from market.models import Class, Subscription


@celery.task
def check_student_inactivity_and_send_emails():
    """Checks for student inactivity and sends notifications to those who haven't had classes in over a week."""
    now = datetime.now(timezone.utc)
    one_week_ago = now - timedelta(days=7)

    lazy_customers = Customer.objects.annotate(
        is_subscribed=Exists(
            Subscription.objects.filter(
                customer=OuterRef('id'),
                is_fully_used=False)
        ),
        active_student=Exists(
            Class.objects.filter(
                customer=OuterRef('id'),
                subscription__isnull=False,
                timeline__end__range=(one_week_ago, now)
            )
        )
    ).filter(
        is_subscribed=True,
        active_student=False
    )

    for user in lazy_customers:
        try:
            send_inactivity_email_to_student(user)
        except Exception as e:
            logger.error(f"Error sending inactivity email to student {user.id}: {e}")


def send_inactivity_email_to_student(customer):
    """This function sends an inactivity warning email to the student using Owl."""
    owl = Owl(
        template='mail/reminder_for_inactive_students.html',
        ctx={'c': customer},
        to=[customer.user.email],
        timezone=customer.user.crm.timezone,
    )
    owl.send()
