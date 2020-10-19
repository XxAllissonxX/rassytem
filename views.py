from django.http import HttpResponse
# from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
import datefinder
from datetime import datetime, timedelta
import csv
import pandas as pd

from .models import CadEmpresa, CadServico, CadVeiculo, TbRastreioParada


def loginPage(request):
    # form = UserCreationForm()
    if request.user.is_authenticated:
        return redirect('person_changelist')
    else:

        if request.method == 'POST':
            username = request.POST.get("username")
            password = request.POST.get("password")

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('person_changelist')
            else:
                messages.info(request, "Username or password is incorrect")

        context = {}
        return render(request, 'hr/login.html', context)


def logoutUser(request):
    logout(request)
    return redirect('login')


def homePage(request):
    cad_empresa = []
    cad_servico = []
    cad_veiculo = []
    tb_rastreio_chamada_list = []

    # Instantiating the future query objects

    cad_empresa = CadEmpresa.objects.all()
    cad_empresa = sorted(cad_empresa.values_list("nome", flat=True))

    # Declaring the objects upon the referred model, and transforming it to a list
    # cad_empresa object is created before request so that can be initialized before the first request comes

    if request.method == "POST":
        form_empresa = [request.POST.get("empresa_cad")]
        form_servico = [request.POST.get("servico_cad")]
        form_veiculo = [request.POST.get("veiculo_cad")]
        form_parada_chamada = [request.POST.get("parada_chamada_tb")]

    # Assigning variable to the get form request objects, even that returns none

    if request.method == "POST" and form_empresa != None:

        if form_empresa == ["Todos"]:
            form_empresa = cad_empresa

        # print("form_empresa", form_empresa)

        id_cad_empresa = CadEmpresa.objects.all().filter(nome__in=form_empresa)
        id_cad_empresa = id_cad_empresa.values_list("id", flat=True)

        # print("id_cad_empresa", id_cad_empresa)

        cad_servico = CadServico.objects.all().filter(cad_empresa_id__in=id_cad_empresa)
        cad_servico = sorted(cad_servico.values_list("nome", flat=True))

        # print("cad_servico", cad_servico)
    # Assigning id from cad_empresa and creating cad_servico query object so that its id can be used in the following form

    if request.method == "POST" and form_servico != None:

        if form_servico == ["Todos"]:
            form_servico = cad_servico

        # print("form_servico", form_servico)

        id_cad_servico = CadServico.objects.all().filter(cad_empresa_id__in=id_cad_empresa, nome__in=form_servico)
        id_cad_servico = id_cad_servico.values_list("id", flat=True)

        # print("id_cad_Servico", id_cad_servico)

        cad_veiculo = CadVeiculo.objects.all().filter(cad_servico_id__in=id_cad_servico)
        cad_veiculo = sorted(cad_veiculo.values_list("nome", flat=True))

        # print("cad_veiculo", cad_veiculo)

    # Assigning id from cad_servico and creating cad_veiculo query object so that its value can be used in the following form

    if request.method == "POST" and form_veiculo != None:

        if form_veiculo == ["Todos"]:
            form_veiculo = cad_veiculo

            # print("form_veiculo", form_veiculo)
        tb_rastreio_parada = TbRastreioParada.objects.all()

        tb_rastreio_chamada = tb_rastreio_parada.filter(placa__in=form_veiculo, servico__in=form_servico)
        tb_rastreio_chamada_list = tb_rastreio_chamada.values_list("chamada", flat=True).distinct()

        # print("tb_rastreio_chamada", tb_rastreio_chamada_list)

    # Assigning tb_rastreio_chamada by using the vehicle plate declared by form_veiculo

    if request.method == "POST" and form_parada_chamada != None:

        if form_parada_chamada == ["Todos"]:
            form_parada_chamada = tb_rastreio_chamada_list

            # print("form_parada_chamada", form_parada_chamada)

        tb_rastreio_parada_date = tb_rastreio_chamada.filter(chamada__in=form_parada_chamada)

        homePage.tb_rastreio_parada_date = tb_rastreio_parada_date

    # Declaring the options "todos" so all fields can be selected, and declaring the attribute "tb_rastrei..." to be used in the csvExport

    return render(request, 'hr/person_form.html',
                  {"cad_empresa": cad_empresa, "cad_servico": cad_servico, "cad_veiculo": cad_veiculo,
                   "tb_rastreio_parada_chamada": tb_rastreio_chamada_list})


def csvExport(request):
    tb_rastreio_parada_date = homePage.tb_rastreio_parada_date

    form_parada_hour_start = request.POST.get("parada_hour_tb_start")
    form_parada_date_start = request.POST.get("parada_date_tb_start")
    form_parada_hour_end = request.POST.get("parada_hour_tb_end")
    form_parada_date_end = request.POST.get("parada_date_tb_end")

    gen_tb_rastreio = []

    final_date = str(datetime.strptime(form_parada_date_end, "%Y-%m-%d") - timedelta(days=1))[:10]
    initial_date = str(datetime.strptime(form_parada_date_start, "%Y-%m-%d") + timedelta(days=1))[:10]

    """

        Na seção abaixo são criados três arrays, cada um responsável por uma parte do filtro de dados. Devido a limitações no banco de dados
        como o campo de data e hora não estar no modelo de carimbo, mas separado em dias e horas, algumas complicações surgiram na filtragem,
        por isso, é criada a seguinte arquitetura. A matriz que termina com "início" obtém todos os valores referentes ao primeiro dia selecionado,
        e filtrar a hora apenas dentro dela, depois disso, o mesmo é feito para o array que termina com "fim", mas para o último dia selecionado, e por fim
        o último array (que fica no meio) são todos os valores entre esses dias selecionados. Depois de atribuir valores a essas matrizes é criado
        um array bufffer que transportará esses arrays para que outro possa transformar todos os três arrays em um único.

    """

    if form_parada_date_start == form_parada_date_end:
        tb_rastreio_parada_hour_start = tb_rastreio_parada_date.filter(data=form_parada_date_start,
                                                                       hora__gte=form_parada_hour_start)
        tb_rastreio_parada_hour_end = tb_rastreio_parada_date.filter(data=form_parada_date_end,
                                                                     hora__lte=form_parada_hour_end)
        tb_rastreio_parada_hour_start = list(tb_rastreio_parada_hour_start.values_list())
        tb_rastreio_parada_hour_end = list(tb_rastreio_parada_hour_end.values_list())
        gen_tb_rastreio.append(tb_rastreio_parada_hour_start)
        gen_tb_rastreio.append(tb_rastreio_parada_hour_end)

        flat_list = [item for sublist in gen_tb_rastreio for item in sublist]

    else:
        tb_rastreio_parada_hour_start = tb_rastreio_parada_date.filter(data=form_parada_date_start,
                                                                       hora__gte=form_parada_hour_start)
        tb_rastreio_parada_hour_end = tb_rastreio_parada_date.filter(data=form_parada_date_end,
                                                                     hora__lte=form_parada_hour_end)
        tb_rastreio_parada_hour = tb_rastreio_parada_date.filter(data__gte=initial_date, data__lte=final_date)
        tb_rastreio_parada_hour = list(tb_rastreio_parada_hour.values_list())
        tb_rastreio_parada_hour_start = list(tb_rastreio_parada_hour_start.values_list())
        tb_rastreio_parada_hour_end = list(tb_rastreio_parada_hour_end.values_list())
        gen_tb_rastreio.append(tb_rastreio_parada_hour_start)
        gen_tb_rastreio.append(tb_rastreio_parada_hour)
        gen_tb_rastreio.append(tb_rastreio_parada_hour_end)

        flat_list = [item for sublist in gen_tb_rastreio for item in sublist]

    """
        In the section below is created the response that will send the data directly to the url defined, "/download/".
        Also, the csv rows are formatted so it can be printed.

    """

    # csvDataFrame = pd.DataFrame(columns=["placa","data","hora","segundos","longitude","latitude","lote", "servico", "chamada"])
    response = HttpResponse(content_type='text/csv')

    csvDataFrame = pd.DataFrame(flat_list)
    csvDataFrame.columns = ["id", "placa", "data", "hora", "segundos", "longitude", "latitude", "lote", "servico",
                            "chamada"]
    csvDataFrame = csvDataFrame.reindex(
        columns=['data', 'placa', 'longitude', 'latitude', 'servico', 'lote', 'chamada', 'hora', 'segundos'])

    response['Content-Disposition'] = 'attachment; filename="tb_rastreio_parada.xlsx"'

    csvDataFrame.to_excel(excel_writer=response, index=False)

    return response











