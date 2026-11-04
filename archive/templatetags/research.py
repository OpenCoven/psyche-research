from django import template
from django.core.exceptions import ValidationError
from archive.forms import validate_artifacts

register=template.Library()

@register.filter
def artifact_links(value):
    try:
        return validate_artifacts(value or '').splitlines()
    except ValidationError:
        return []
