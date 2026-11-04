from getpass import getpass
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help='Human operator only: provision one contributor after approved onboarding. No email or external identity required.'
    def add_arguments(self,parser):
        parser.add_argument('username')
    def handle(self,*args,**options):
        user=get_user_model()(username=options['username'])
        try:
            user.full_clean(exclude=['password'])
            password=getpass('Initial password (share through the approved private route): ')
            if password!=getpass('Confirm password: '):
                raise CommandError('Passwords did not match.')
            validate_password(password,user)
            user.set_password(password)
            user.save()
        except ValidationError as exc:
            raise CommandError('; '.join(exc.messages))
        self.stdout.write('Contributor provisioned. Ask the human to change the initial password after sign-in.')
