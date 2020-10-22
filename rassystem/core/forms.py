from django import forms
from core.models import Company, Service, Vehicle, Call

CHOICES = (('Rastreio', 'Rastreio'), ('Parada', 'Parada'))


class CallFilterForm(forms.Form):

    company = forms.ModelChoiceField(Company.objects.all())
    services = forms.ModelMultipleChoiceField(Service.objects.all())
    vehicles = forms.ModelMultipleChoiceField(Vehicle.objects.all())
    kinds = forms.MultipleChoiceField(choices=CHOICES)
    call_initial_date = forms.SplitDateTimeField()
    call_end_date = forms.SplitDateTimeField()
