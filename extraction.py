#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import requests
import sys
import pymysql
import schedule
from datetime import timedelta
from datetime import datetime


# In[2]:


def connection():
    """Conecta com o banco de dados.
    
    c, conn = connection()
    
    Return
    ----------------------
    c    : cursor - objeto. 
    conn : connection - objeto.

    """
    conn = pymysql.connect(user='root',
                           password='',
                           db='tpf',
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    c = conn.cursor()
    return c, conn


# In[3]:


def get_rotulos(x):
    """Acessa a API que fornece os rótulos, também chamados de serviços, de determinada empresa.
       
    df = get_rotulos(x)
    
    Parameters
    ----------
    x    : id da empresa - int. 
    
    Return
    ----------------------
    df    : dataframe com os rótulos de determinada empresa - dataframe. 

    """
    df = pd.DataFrame((requests.get('http://backend.rassystem.com.br/app/v1/api/filiais/' + str(x) + '/rotulos',
                                    auth=('', ''))).json())
    df['cad_empresa_id'] = df_filiais[df_filiais['idFilial'] == x]['idFilial'].values[0]
    return df


# In[4]:


def get_veiculo(id):
    """Acessa a API que fornece os veículos de determinado rótulo.
       
    df = get_veiculo(id)
    
    Parameters
    ----------
    id  : id do rótulo - int. 
    
    Return
    ----------------------
    df    : dataframe com os veículos de determinado rótulo - dataframe. 

    """
    df_veiculos = pd.DataFrame(
        requests.get('http://backend.rassystem.com.br/app/v1/api/rotulos/' + str(id) + '/veiculos',
                     auth=('', '')).json())
    df_veiculos['cad_servico_id'] = id
    df_veiculos['lote'] = \
        df_filiais[df_filiais['idFilial'] == df_rotulos[df_rotulos['id'] == id]['cad_empresa_id'].values[0]][
            'nome'].values[
            0]
    df_veiculos['servico'] = df_rotulos[df_rotulos['id'] == id]['nome'].values[0]
    return (df_veiculos)


# In[5]:


f = lambda x: dict(x['properties'], **{'longitude': x['geometry']['coordinates'][0]},
                   **{'latitude': x['geometry']['coordinates'][1]})


# In[6]:


def get_rastreio(id, servico, data_start, data_end):
    """Acessa a API que fornece os rastreios de determinado veículo.
       
    df = get_rastreio(id, data_start, data_end)
    
    Parameters
    ----------
    id  : id do veículo - int. 
    data_start: data de ínicio da consulta - string no formato "%Y-%m-%dT07:30:00-03:00"
    data_end: data de fim da consulta - string no formato "%Y-%m-%dT07:30:00-03:00"
    
    Return
    ----------------------
    df    : dataframe com os dados de  rastreios do veículo -  dataframe. 

    """
    req = requests.get("http://backend.rassystem.com.br/app/v1/api/veiculos/" + str(
        int(id)) + "/rastreio?dataInicio=" + data_start + "&dataFim=" + data_end, auth=('', ''))
    if req.status_code == 200:
        df = pd.DataFrame((map(f, req.json()['features'])))
        df['servico'] = servico
        return df


# In[8]:


def get_parada(id, servico, data_start, data_end):
    """Acessa a API que fornece os dados de parada de determinado veículo.
       
    df = get_parada(id, data_start, data_end)
    
    Parameters
    ----------
    id  : id do veículo - int. 
    data_start: data de ínicio da consulta - string no formato "%Y-%m-%dT07:30:00-03:00"
    data_end: data de fim da consulta - string no formato "%Y-%m-%dT07:30:00-03:00"
    
    Return
    ----------------------
    df    : dataframe com os dados de parada do veículo -  dataframe. 

    """
    req = requests.get("http://backend.rassystem.com.br/app/v1/api/veiculos/" + str(
        int(id)) + "/paradas?dataInicio=" + data_start + "&dataFim=" + data_end, auth=('', ''))
    if req.status_code == 200:
        df = pd.DataFrame((map(f, req.json()['features'])))
        df['servico'] = servico
        return df


# In[11]:


def proc(df):
    """Processa o dataframe com dados de rastreio ou dados de parada para conter as informações de 
    data, hora, serviço, lote, chamada e placa.
       
    df = proc(df)
    
    Parameters
    ----------
    df : dataframe com os dados de parada ou rastreio do veículo -  dataframe. 

    
    Return
    ----------------------
    df : dataframe processado com os dados de parada ou rastreio do veículo -  dataframe. 

    """
    placa = lambda x: df_veiculos[df_veiculos['id'] == x]['nome'].iloc[0]
    # df['servico'] = df['idVeiculo'].apply(lambda x: df_veiculos[df_veiculos['id'] == x]['servico'].iloc[0])
    df['lote'] = df['idVeiculo'].apply(lambda x: df_veiculos[df_veiculos['id'] == x]['lote'].iloc[0])
    df['chamada'] = 'parada' if ('segundos' in df.columns) else 'rastreio'
    df['hora'] = df['data'].apply(lambda x: x.split('T')[1].split('.')[0])
    df['data'] = df['data'].apply(lambda x: x.split('T')[0])
    df['idVeiculo'] = df['idVeiculo'].apply(placa)
    return df


# In[12]:


def get_dataframes(data_start, data_end):
    """Chama as funções para consultar as API's nos limites entre data_start e data_end 
    e obter os dados de parada e rastreio para todos os veículos cadastrados em todos os
    serviços de todas as empresas. 
       
    df_filiais, df_rotulos, df_veiculos, df = get_dataframes(data_start, data_end)
    
    Parameters
    ----------
    data_start: data de ínicio da consulta - string no formato "%Y-%m-%dT07:30:00-03:00"
    data_end: data de fim da consulta - string no formato "%Y-%m-%dT07:30:00-03:00" 

    
    Return
    ----------------------
    df_filiais = dataframe com os dados das empresas - dataframe.
    df_rotulos = dataframe com os dados dos serviço  - dataframe.
    df_veiculos = dataframe com os dados dos veículos - dataframe.
    df : dataframe com os dados de parada ou rastreio do veículo -  dataframe. 

    """
    req = requests.get('http://backend.rassystem.com.br/app/v1/api/filiais', auth=('', ''))
    global df_filiais
    global df_rotulos
    global df_veiculos
    df_filiais = pd.DataFrame(req.json())
    df_rotulos = pd.concat(map(get_rotulos, df_filiais['idFilial']))
    df_veiculos = pd.concat(map(get_veiculo, df_rotulos['id']))

    df_veiculos.rename(columns={'placa': 'nome'}, inplace=True)

    ids = df_veiculos['id']

    servico = df_veiculos['servico']

    len_ids = len(ids)

    df_parada = pd.concat(map(get_parada, ids, servico, [data_start] * len_ids, [data_end] * len_ids))

    df_rastreio = pd.concat(map(get_rastreio, ids, servico, [data_start] * len_ids, [data_end] * len_ids))

    return df_filiais, df_rotulos, df_veiculos, pd.concat(map(proc, [df_rastreio, df_parada])).rename(
        columns={'idVeiculo': 'placa'})


# In[67]:


def rotina():
    """Gerencia as extrações e insere os dados no banco de dados  
       
    rotina()
    

    """
    c, conn = connection()
    c.execute("select * from tb_log_extracao")
    conn.close()
    df_log_extracao = pd.DataFrame(c)
    # display(df_log_extracao)
    date_fail = df_log_extracao[df_log_extracao['status'] == 'fail'][['id', 'date_start', 'date_end']].values

    for i in date_fail:

        try:

            df_filiais, df_rotulos, df_veiculos, df = get_dataframes(i[1], i[2])
            df = df.where((pd.notnull(df)), None)
            c, conn = connection()
            c.executemany(
                "insert into tb_rastreio_parada (" + ', '.join(df.columns) + ") values (" + ("%s, " * len(df.columns))[
                                                                                            :-2] + ")",
                [tuple(row) for row in df.values])
            c.execute(r'update tb_log_extracao set status = %s where ID = %s', ('sucess', i[0]))
            conn.commit()
        except:
            pass

    try:

        data_start = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT07:30:00-03:00")
        data_end = (datetime.now()).strftime("%Y-%m-%dT07:30:00-03:00")
        if data_end not in df_log_extracao[df_log_extracao['status'] == 'sucess']['date_end'].values:
            print(data_start, data_end)
            df_filiais, df_rotulos, df_veiculos, df = get_dataframes(data_start, data_end)

            df = df.where((pd.notnull(df)), None)
            c, conn = connection()
            c.execute("delete from cad_veiculo")
            c.executemany("insert into cad_veiculo (" + ', '.join(df_veiculos.columns) + ") values (" + ("%s, " * len(
                df_veiculos.columns))[:-2] + ")",
                          [tuple(row) for row in df_veiculos.values])
            c.executemany(
                "insert into tb_rastreio_parada (" + ', '.join(df.columns) + ") values (" + ("%s, " * len(df.columns))[
                                                                                            :-2] + ")",
                [tuple(row) for row in df.values])
            conn.commit()
            conn.close()
            print('pronto')
            c, conn = connection()
            c.execute("insert into tb_log_extracao (date_start, date_end, status) values (%s, %s, %s)",
                      [data_start, data_end, 'sucess'])
            conn.commit()

    except Exception as e:

        exc_type, exc_obj, exc_tb = sys.exc_info()
        print(str(e))
        c, conn = connection()
        c.execute("insert into tb_log_extracao (date_start, date_end, status, log) values (%s, %s, %s,%s)",
                  [data_start, data_end, 'fail', str(e)])
        conn.commit()


def main():
    schedule.every().day.at("09:30").do(rotina)

    while True:
        schedule.run_pending()


if __name__ == "__main__":
    main()
