"""Rendered error navigation; fixtures contain no participant information."""
from django import forms
from django.template.loader import render_to_string
from django.test import SimpleTestCase


class FormErrorSummaryTests(SimpleTestCase):
    def test_summary_links_visible_errors_to_prefixed_controls_and_escapes_text(self):
        class ExampleForm(forms.Form):
            title = forms.CharField(label='Title <synthetic>')
            confirmation = forms.BooleanField(label='Rights confirmation')
            revision = forms.IntegerField(widget=forms.HiddenInput)

        form = ExampleForm({'draft-title': '', 'draft-revision': 'invalid'}, prefix='draft')
        form.add_error(None, 'Synthetic <script>never execute</script>')
        html = render_to_string('archive/_form.html', {'form': form})
        self.assertIn('aria-label="Form errors"', html)
        for name in ('title', 'confirmation'):
            field_id = form[name].id_for_label
            self.assertIn(f'href="#{field_id}"', html)
            self.assertIn(f'id="{field_id}"', html)
            self.assertIn(f'for="{field_id}"', html)
        self.assertNotIn('href="#id_draft-revision"', html)
        self.assertIn('Revision: Enter a whole number.', html)
        self.assertIn('Title &lt;synthetic&gt;:', html)
        self.assertIn('Synthetic &lt;script&gt;never execute&lt;/script&gt;', html)
        self.assertNotIn('<script>', html)
        self.assertIn('aria-invalid="true"', html)

    def test_valid_and_unbound_forms_have_no_error_summary_and_preserve_values(self):
        class ExampleForm(forms.Form):
            title = forms.CharField()

        for form in (ExampleForm(), ExampleForm({'title': 'SYNTHETIC retained text'})):
            with self.subTest(bound=form.is_bound):
                html = render_to_string('archive/_form.html', {'form': form})
                self.assertNotIn('aria-label="Form errors"', html)
                self.assertNotIn('href="#id_title"', html)
                if form.is_bound:
                    self.assertIn('value="SYNTHETIC retained text"', html)
