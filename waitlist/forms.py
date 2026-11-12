import unicodedata
from django import forms
from .models import Registration


class RegistrationForm(forms.Form):
    email = forms.EmailField(max_length=254, widget=forms.EmailInput(attrs={'autocomplete': 'email', 'inputmode': 'email'}))
    interest = forms.ChoiceField(choices=[('', 'Choose your interest')] + Registration._meta.get_field('interest').choices,
                                error_messages={'invalid_choice': 'Choose reader, researcher / contributor, or both.'})
    name = forms.CharField(max_length=100, required=False, label='Name (optional)', widget=forms.TextInput(attrs={'autocomplete': 'name'}))
    consent = forms.BooleanField(label='I agree to the waitlist privacy notice and to receive updates about Psyche Research availability.')
    website = forms.CharField(required=False, max_length=200, widget=forms.HiddenInput)

    def clean_email(self):
        return self.cleaned_data['email'].strip().casefold()

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if any(unicodedata.category(char).startswith('C') for char in name):
            raise forms.ValidationError('Use a name without control characters.')
        return name

