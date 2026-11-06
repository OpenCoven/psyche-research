import ipaddress
from urllib.parse import urlsplit
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from .models import Submission, CONTENT_FIELDS, Capacity


class BrowserMaxLengthValidator(MaxLengthValidator):
    """HTML maxlength uses UTF-16 units, including for non-BMP writing scripts."""

    def clean(self, value):
        return len(value) + sum(ord(character) > 0xffff for character in value)


class SubmissionTextField(forms.CharField):
    """Normalize browser line endings before validating or storing new input."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validators = [BrowserMaxLengthValidator(validator.limit_value)
                           if isinstance(validator, MaxLengthValidator) else validator
                           for validator in self.validators]
        if self.max_length is not None:
            self.help_text = f'{self.help_text} At most {self.max_length:,} characters.'.strip()

    def to_python(self, value):
        value = super().to_python(value)
        return value.replace('\r\n', '\n').replace('\r', '\n')

# Shown on the public policies page; keep the enforced bound and the published description identical.
MAX_ARTIFACT_LINKS = 8

def validate_artifacts(text):
    urls = [x.strip() for x in text.splitlines() if x.strip()]
    if len(urls) > MAX_ARTIFACT_LINKS:
        raise ValidationError('Use at most eight public artifact links.')
    for url in urls:
        try:
            parts = urlsplit(url)
            host = (parts.hostname or '').lower().rstrip('.')
            if (len(url) > 2000 or any(c.isspace() or ord(c) < 32 or c in '<>"\\' for c in url) or
                parts.scheme != 'https' or parts.username or parts.password or parts.query or
                parts.port not in (None,443) or not host or '.' not in host or
                host.endswith(('.local','.internal','.localhost')) or host == 'localhost'):
                raise ValueError()
            try:
                addr = ipaddress.ip_address(host.strip('[]'))
            except ValueError:
                addr = None
            if addr and not addr.is_global:
                raise ValueError()
            host.encode('idna')
        except (ValueError, UnicodeError):
            raise ValidationError('Use public HTTPS artifact URLs without credentials, query tokens, local hosts or private IP addresses. Links are never fetched by the archive.')
    return '\n'.join(urls)

class SubmissionForm(forms.ModelForm):
    revision = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    class Meta:
        model = Submission
        fields = list(CONTENT_FIELDS) + ['rights_confirmed','privacy_confirmed']
        field_classes = {name: SubmissionTextField for name in CONTENT_FIELDS
                         if name not in ('kind', 'license')}
        help_texts = {
            'byline': 'Names shown publicly on publication. Obtain every named contributor’s consent; affiliation is optional.',
            'methods': 'Describe what you did, evaluation conditions, and enough detail to inspect or replicate it. Plain text or public methods links.',
            'claims': 'Separate measured observations from interpretation. Negative and inconclusive results are welcome.',
            'limitations': 'State uncertainty, missing controls, constraints and what the evidence does not establish.',
            'artifacts': 'One stable public HTTPS link per line, up to eight. No credentials, signed URLs or query strings. We do not fetch links or accept file uploads.',
            'provenance': 'Where data, code and materials came from, permissions, relevant versions, and any restrictions.',
            'license': 'License for the submitted text and metadata. Linked artifacts retain their own licenses.',
            'ai_disclosure': 'Name AI assistance and what it did, or write “None”. Authors remain responsible.',
            'change_note': 'Required for a later version: explain the correction or substantive change.',
            'rights_confirmed': 'I have permission to publish the submitted material and list the named authors.',
            'privacy_confirmed': 'I checked for private data, credentials, restricted material and unsafe disclosures.'}
        widgets = {k: forms.Textarea(attrs={'rows': 5}) for k in ['abstract','methods','claims','limitations','artifacts','provenance','ai_disclosure','change_note']}
    def clean_artifacts(self):
        return validate_artifacts(self.cleaned_data.get('artifacts',''))

class DecisionForm(forms.Form):
    conflicts = forms.CharField(max_length=2000, widget=forms.Textarea, help_text='Describe relevant conflicts, or explicitly state None. This is human moderation, not independent scientific peer review.')
    revision = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    action = forms.ChoiceField(choices=[('changes','Request changes'),('decline','Decline'),('publish','Publish exact submitted version')])
    reason = forms.CharField(max_length=2000, widget=forms.Textarea, help_text='Private reason visible to the author. Moderation is a scope, rights, privacy, safety and completeness check, not scientific validation.')

class ReasonForm(forms.Form):
    reason = forms.CharField(max_length=2000, widget=forms.Textarea)

class WithdrawalForm(forms.Form):
    reason = forms.CharField(max_length=1000, widget=forms.Textarea, help_text='This reason becomes public. Omit private or unsafe details. All versions become tombstones.')

class CapacityForm(forms.ModelForm):
    revision = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    reason = forms.CharField(max_length=1000)
    class Meta:
        model = Capacity
        fields = ['intake_open','queue_limit','per_author_limit','draft_limit']
