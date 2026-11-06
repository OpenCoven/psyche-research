"""Human operator links an immutable provider subject to an existing local account."""
import re
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, IntegrityError
from archive.models import Event, WorkOSIdentity


class Command(BaseCommand):
    help = 'Link or disable an existing account WorkOS identity without creating accounts or granting roles.'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True)
        parser.add_argument('--client-id', required=True)
        parser.add_argument('--subject', required=True)
        parser.add_argument('--reason', required=True)
        parser.add_argument('--disable', action='store_true')

    def handle(self, *args, **options):
        client_id, subject, reason = options['client_id'], options['subject'], options['reason'].strip()
        if (not re.fullmatch(r'client_[A-Za-z0-9]{1,120}', client_id)
            or not re.fullmatch(r'user_[A-Za-z0-9]{1,120}', subject) or not reason or len(reason) > 500):
            raise CommandError('Provide valid client/subject identifiers and a bounded operator reason; values are not logged.')
        try:
            with transaction.atomic():
                user = get_user_model().objects.select_for_update().get(username=options['username'])
                identity = WorkOSIdentity.objects.filter(user=user).first()
                if options['disable']:
                    if not identity or (identity.client_id, identity.subject) != (client_id, subject):
                        raise CommandError('The expected identity does not match; no binding changed.')
                    if not identity.enabled:
                        self.stdout.write('Identity is already disabled; no change.')
                        return
                    identity.enabled = False
                    identity.save(update_fields=['enabled'])
                else:
                    if identity:
                        raise CommandError('This local account already has a binding. Relinking or re-enabling needs separate review; no change.')
                    WorkOSIdentity.objects.create(user=user, client_id=client_id, subject=subject)
                Event.objects.create(kind='workos_identity_disabled' if options['disable'] else 'workos_identity_linked',
                    target=str(user.pk), details={'client_id': client_id, 'subject': subject, 'reason': reason})
        except get_user_model().DoesNotExist:
            raise CommandError('Local account does not exist; no identity created.') from None
        except IntegrityError:
            raise CommandError('Identity is already bound or a concurrent change occurred; no change.') from None
        self.stdout.write('WorkOS identity updated and audited. Local roles are unchanged.')
