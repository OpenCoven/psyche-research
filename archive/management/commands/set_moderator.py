from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from archive.models import Event

class Command(BaseCommand):
    help='Human operator only: grant or revoke explicit moderator access after separate approval.'
    def add_arguments(self,parser):
        parser.add_argument('username')
        parser.add_argument('--revoke',action='store_true')
        parser.add_argument('--reason',required=True)
    @transaction.atomic
    def handle(self,*args,**options):
        try:
            user=get_user_model().objects.get(username=options['username'],is_active=True)
        except get_user_model().DoesNotExist:
            raise CommandError('Active contributor not found.')
        if not options['reason'].strip() or len(options['reason'])>1000:
            raise CommandError('Provide a reason of at most 1,000 characters.')
        group=Group.objects.get(name='moderators')
        if options['revoke']:
            user.groups.remove(group)
        else:
            user.groups.add(group)
        Event.objects.create(actor=None,kind='operator_role_revoked' if options['revoke'] else 'operator_role_granted',target=str(user.pk),details={'reason':options['reason']})
        self.stdout.write('Explicit moderator role updated and audited; this does not authorize self-approval.')
