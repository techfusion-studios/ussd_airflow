from django.urls import re_path
from ussd.views import MermaidText, ValidateJourney

urlpatterns = [
    re_path(r'mermaid_text$', MermaidText.as_view(), name="mermaid_text"),
    re_path(r'validate_journey$', ValidateJourney.as_view())
]