from django import forms
from core.models import Company, Service, Vehicle, Call


class CallFilterForm(forms.Form):

    company = forms.ModelChoiceField(Company.objects.all())
    services = forms.ModelMultipleChoiceField(Service.objects.all())
    vehicles = forms.ModelMultipleChoiceField(Vehicle.objects.all())
    calls = forms.ModelMultipleChoiceField(Call.objects.all())
    call_initial_date = forms.SplitDateTimeField()
    call_end_date = forms.SplitDateTimeField()
