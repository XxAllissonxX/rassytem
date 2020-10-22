from django.shortcuts import render
from django.views.generic import FormView, TemplateView
from django.http import HttpResponseRedirect
from django.shortcuts import render
from core.forms import CallFilterForm
from core.models import Call


class CallFilterView(FormView):
    form_class = CallFilterForm
    success_url = ''
    template_name = 'core/call_filter_form.html'


class CallFilteredListView(TemplateView):

    template_name = 'core/call_filtered_list.html'

    def post(self, request, *args, **kwargs):
        form = CallFilterForm(self.request.POST)

        if form.is_valid():
            company = form.cleaned_data['company']
            services = form.cleaned_data['services']
            vehicles = form.cleaned_data['vehicles']
            kinds = form.cleaned_data['kinds']
            call_initial_date = form.cleaned_data['call_initial_date']
            call_end_date = form.cleaned_data['call_end_date']
            context = {}
            context['call_list'] = Call.objects.filter(
                company=company,
                vehicle__in=vehicles,
                service__in=services,
                kind__in=kinds,
                call_date__range=(call_initial_date, call_end_date))

            return render(request, self.template_name, context)

        return render(request, self.template_name, {'call_list': []})
