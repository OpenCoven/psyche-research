from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from archive.models import Capacity,Event

class Command(BaseCommand):
    help='Pause intake without a browser. Never opens intake.'
    def add_arguments(self,parser):
        parser.add_argument('--reason',required=True)
    @transaction.atomic
    def handle(self,*args,**options):
        reason=options['reason'].strip()
        if not reason or len(reason)>1000:
            raise CommandError('Provide a bounded pause reason.')
        row=Capacity.objects.select_for_update().get(pk=1)
        row.intake_open=False
        row.revision+=1
        row.save()
        Event.objects.create(actor=None,kind='operator_intake_paused',target='capacity',details={'reason':reason})
        self.stdout.write('Intake paused; drafts and public archive are unchanged.')
