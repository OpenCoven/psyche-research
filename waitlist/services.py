"""No private values are logged, returned or sent to third parties."""
import hashlib
import hmac
from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from .models import AddressBudget, CollectionState, Registration


def register(cleaned):
    """Return accepted/busy/paused/limited; accepted covers duplicates and honeypots."""
    if not settings.WAITLIST_COLLECTION_ENABLED:
        return 'paused'
    now = timezone.now()
    minute, day = int(now.timestamp()) // 60, int(now.timestamp()) // 86400
    with transaction.atomic():
        state = CollectionState.objects.select_for_update().get(pk=1)
        if state.paused:
            return 'paused'
        if state.minute != minute:
            state.minute, state.minute_attempts = minute, 0
        if state.day != day:
            state.day, state.day_attempts = day, 0
        if state.minute_attempts >= 30 or state.day_attempts >= 200:
            return 'limited'
        state.minute_attempts += 1
        state.day_attempts += 1
        state.save(update_fields=['minute', 'minute_attempts', 'day', 'day_attempts'])
        if cleaned.get('website'):
            return 'accepted'
        key = hmac.new(settings.SECRET_KEY.encode(), f"{day}:{cleaned['email']}".encode(), hashlib.sha256).hexdigest()
        AddressBudget.objects.filter(expires_at__lte=now).delete()
        budget, _ = AddressBudget.objects.get_or_create(key=key, defaults={'expires_at': now + timedelta(days=1)})
        if budget.attempts >= 3:
            return 'limited'
        budget.attempts += 1
        budget.save(update_fields=['attempts'])
        if state.retained_count >= settings.WAITLIST_CAPACITY:
            # Same response for new and existing addresses at capacity.
            return 'paused'
        # Runtime can SELECT only email, not private name/interest/consent/time.
        if Registration.objects.filter(email=cleaned['email']).exists():
            return 'accepted'
        Registration.objects.bulk_create([Registration(email=cleaned['email'], name=cleaned['name'],
            interest=cleaned['interest'], privacy_version=settings.WAITLIST_PRIVACY_VERSION)])
        state.retained_count += 1
        state.save(update_fields=['retained_count'])
    return 'accepted'

