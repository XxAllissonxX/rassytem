# Importando a Biblioteca PyMysql, requests e array
import mysql.connector
import requests
import json

conexao = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='veiculos'
)
cursor = conexao.cursor(buffered=True)

cursor.execute("select idveiculo from cad_veiculo where lote = '1' and servico = 'SERVICOS'")

# for x in cursor:
#     for y in x:
#         print(y)

data_inicio = input('Digite a data de inicio que deseja consultar (ex: AAAA-MM-DD):')
data_fim = input('Digite a data de fim que deseja consultar (ex: AAAA-MM-DD): ')

# Na lista (veiculo =[]) são armazenados todos os ids da consulta
veiculos = []
for x in cursor:
    veiculos.append(x)

# Aqui pego os ids e passo na url da api para pegar os dados de json de cada id.
for y in veiculos:
    print("-------------------")
    print("-------------------{}".format(y))
    print("-------------------")
    req = requests.get(
        f'http://backend.rassystem.com.br/app/v1/api/veiculos/{y[0]}/rastreio?dataInicio={data_inicio}T07:30:00-03:00&dataFim={data_fim}T07:30:00-03:00',
        auth=('', ''))
    dados = req.json()

    # Faço a iteração dos resultados do json, so preciso desses 4 dados da api (idveiculo, data, latitude e longitude)
    for i in dados['features']:
        idveiculo = i['properties']['idVeiculo']
        data = i['properties']['data']
        longitude = i['geometry']['coordinates'][0]
        latitude = i['geometry']['coordinates'][1]

        # Query de inserção dos dados em outra tabela (log)
        insert_query = "INSERT INTO log_rastreio(idveiculo, data, longitude, latitude, lote, servico) " \
                       "VALUES ('" + str(idveiculo) + "','" + data + "','" + str(longitude) + "','" + str(
            latitude) + "','" + str('1') + "','" + str('SERVICOS') + "')"
        print(insert_query)
        cursor.execute(insert_query)

conexao.commit()
