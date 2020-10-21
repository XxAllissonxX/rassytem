from django.shortcuts import render
from django.views.generic import FormView
from core.forms import CallFilterForm


class CallFilterView(FormView):
    form_class = CallFilterForm
    success_url = ''
    template_name = 'core/call_filter_form.html'
