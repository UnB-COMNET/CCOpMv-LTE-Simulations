# -*- coding: utf-8 -*-
"""

Importar as bibliotecas do Pandas, Numpy, Sklearn

"""

import time
import pandas as pd
import numpy as np
import plotly.express as px
import re
from pathlib import Path
from typing import Dict, List, Union
import general_functions as genf
from errors import check_mode
import sys
import plotly.graph_objs as go
import os
from math import sqrt
import scipy.stats as stats
"""## Sobre:

4000 x 4000 - 60 UE - 100 setores

Tempo de simulação: 10 execuções (slices) de 5s cada

Repetições: 5

Modificações: 
* Scenario: URBAN_MACROCELL -> URBAN_MICROCELL
* Potencia eNB: 46 dBm -> 30 dBm
* Ganho UE: 0 -> -1
* Acarretou mudança no SINR

Casos:

* **min sinr - ENBs**
* 100 sinr - [11, 13, 15, 18, 31, 38, 52, 66, 68, 70, 83, 87]
* 60 sinr - [12, 22, 26, 28, 47, 50, 64, 68, 87, 92]
* 40 sinr - [12, 18, 26, 53, 68, 70, 77, 84]
* 10 sinr - [18, 22, 27, 71, 77]
* 5 sinr - [5, 30, 68, 74]

App: UDP Video Streaming (INET)

* Pacote: 1428B
* Intervalo de envio: 1.1424ms
* Tamanho do vídeo: 10 MiB
* Max: 10Mbps
* Pacotes max: 875,35 pkt/s (total max de 8753 pacotes, 8750 no sliced)

# **Dados**

## **Leitura dos Dados**

Data generated using the command: 

    opp_scavetool x -o ilp_varying_sliced_video.csv -f "module(**.cellularNic.channelModel[*]) OR module(**.app[*])" ilp_varying_sliced_*_VIDEO/*-*.sca ilp_varying_sliced_*_VIDEO/*-*.vec
"""

COLOR_AID = "firebrick"
COLOR_TID = "springgreen"
COLOR_PGWO = "dodgerblue"
COLOR_PGD = "darkmagenta"

def get_data_from_scalar (data_name: str, module: str, scalar_data) -> pd.DataFrame:

  raw_module = scalar_data.apply(lambda x: x["module"][x["module"].find('.')+1:], axis=1)

  qname = raw_module + '.' + scalar_data.name

  pre_data = scalar_data.assign(qname = qname)

  data = pre_data[raw_module.str.match(module)]
  data = data[data["name"].str.startswith(data_name)]
  data = data.pivot(index='run', columns='qname', values='value')
  #count = num_ues*num_macros - data.isnull().sum(axis=1)

  return data

def get_data_from_vector (data_name: str, module: str, vector_data):

  raw_module = vector_data.apply(lambda x: x["module"][x["module"].find('.')+1:], axis=1)

  qname = raw_module + '.' + vector_data.name

  pre_data = vector_data.assign(qname = qname)

  data = pre_data[raw_module.str.match(module)]
  data = data[data["name"].str.startswith(data_name)]
  data = data.pivot(index='run', columns='qname', values=['vecvalue', 'vectime'])
  #count = num_ues*num_macros - data.isnull().sum(axis=1)

  return data

# data_ul must have collumns names with at least 2 numbers
# data_plot is the data with other informations about each simulation
# the return new_data_plot is the data_plot Dataframe plus information in return data 
# limit is maximum not included value that is wanted
# num_ues_total is used to calculate the count and mean values
# num_ues and directions are used to get the applications from the same UE both in the dl and ul data
def gen_ues_data(data_ul, data_dl, limit: float, num_ues_total: int, num_ues: int, directions: int, data_plot, multi: bool = False):

  data = pd.DataFrame()
  for a in data_ul:
    p = re.findall(r'\d+', a)
    i = [int(s) for s in p]
    data[i[0]] = data_ul[a]

  for b in data_dl:
    p = re.findall(r'\d+', b)
    i = [int(s) for s in p]

    if multi:
      data[i[0]*num_ues*directions + i[1]] = data[i[0]*num_ues*directions + i[1]].add(data_dl[b])
    else:
      data[i[0]] = data[i[0]].add(data_dl[b])

  count = num_ues_total - data.isnull().sum(axis=1) - (data >= limit).sum(axis=1)
  nan_count = data.isnull().sum(axis=1)
  mean = data.sum(axis=1).divide(num_ues_total - nan_count)

  percentage = count / num_ues_total * 100
  n_percentage = ((count*-1).sub(nan_count) + num_ues_total) / num_ues_total * 100
  nan_percentage = nan_count / num_ues_total * 100

  new_data_plot = pd.concat([data, data_plot], axis= 1)
  new_data_plot = new_data_plot.assign(count = count, nan_count = nan_count, mean = mean, percentage = percentage,
                                       n_percentage = n_percentage, nan_percentage = nan_percentage)

  return new_data_plot, data

def gen_ues_data_single(data, num_ues: int, directions: int, multi: bool = False):
  new_data = pd.DataFrame()
  macro = pd.DataFrame()
  micro = pd.DataFrame()

  for a in data.columns:
    p = re.findall(r'\d+', a)
    i = [int(s) for s in p] #Acha dois numeros

    if multi:#If multiple ues groups (ex: ue0[], ue1[])
      new_data[i[0]*num_ues*directions + i[1]] = data[a]
    else:
      new_data[i[0]] = data[a]

  return new_data

def unite_slices (processed_data: pd.DataFrame, extra_info: pd.DataFrame, id_columns: list, nonactive_ues: pd.DataFrame, ues_per_slice: dict, slice_op= 'mean', count_enb = False, col_to_keep = "NumEnbs"):

  dropna = False

  noslice_data: pd.DataFrame

  seeds = []

  for name in processed_data.index:
    p = re.compile(r'seed_\d+')
    m = p.search(name)
    if m:
      numbers = re.compile(r'\d+')
      seed = numbers.search(m.group())
      seeds.append(int(seed.group()))
    else:
      print('ERROR: Não foi possível determinar a seed.')

  data = pd.concat([processed_data, extra_info[id_columns]], axis= 1).assign(seed=seeds, Slice=extra_info['Slice'].astype(int))

  new_data = data.copy()

  #tuples_to_na = []

  print('Identifying not active UEs.')
  for _seed in np.unique(seeds):
    list_slices = ues_per_slice[str(_seed)]
    for i in range(len(list_slices)):
      tmp_sel = new_data[new_data['seed'] == _seed]
      selected = tmp_sel[tmp_sel['Slice'] == i]
      #print(f'Slice: {i}')
      for min_snr in extra_info['min_snr_used'].unique():
        if nonactive_ues.index.droplevel('run').isin([(_seed, i, int(min_snr))]).any():
          #print(f'MinSnr: {min_snr}')
          tmp_sel = new_data[new_data['seed'] == _seed]
          tmp_sel2 = tmp_sel[tmp_sel['min_snr_used'] == min_snr]
          selected = tmp_sel2[tmp_sel2['Slice'] == i]
          for column in selected.columns:
            p = re.compile(fr'ue\[\d+\]')
            m = p.search(column)
            if m is not None: #If its not a extra info column
              p2 = re.compile(r'\d+')
              m2 = p2.search(m.group())
              if m2 is not None:
                if int(m2.group()) not in list_slices[i]:
                  new_data.loc[selected.index, column] = np.nan
                else:
                  isnt_active = np.all(nonactive_ues.loc[(_seed, i, int(min_snr)), int(m2.group())])
                  if isinstance(isnt_active, pd.DataFrame) or isinstance(isnt_active, pd.Series):
                    print("ERROR: missing aditional id values for nonactive_ues")
                  if isnt_active:
                    new_data.loc[selected.index, column] = np.nan
                    pass
  
  if count_enb:
    new_data["NumSliceMaxEnbs"] = [0]*new_data.shape[0]
    new_data["MeanNumSliceConstEnbs"] = [0]*new_data.shape[0]
    new_data["MeanNumSliceConstEnbs++1"] = [0]*new_data.shape[0]
    new_data["MaxAddEnbs"] = [0]*new_data.shape[0]
    new_data["NumAddNumEnbs"] = [0]*new_data.shape[0]
    new_data["MeanAddNumEnbs"] = [0]*new_data.shape[0]
    new_data["NumAddNumEnbsw0"] = [0]*new_data.shape[0]
    new_data["MeanAddNumEnbsw0"] = [0]*new_data.shape[0]

    for min_snr in extra_info['min_snr_used'].unique():
      #min_snr = '15' #TODO: REMOVE
      
      test_data = data.copy()
      test_data = test_data[test_data['min_snr_used'] == min_snr]
      pivot_df = test_data.pivot(index='Slice', columns='seed', values='NumEnbs')
      pivot_df.columns = ['seed_' + str(col) for col in pivot_df.columns]
      
      for seed in np.unique(seeds):
        enb_list = pivot_df['seed_'+str(seed)].to_list()

        max_enb = max(enb_list) 
        num_add_enb = len(set(enb_list))  # 5 NumAddNumEnbs
        
        derivative = []
        derivative.append(enb_list[0])
        for i in range(1, len(enb_list)):
          diff = enb_list[i] - enb_list[i - 1]
          derivative.append(diff)
        
        max_add_enb = max(derivative) # 4 MaxAddEnbs

        derivative_diff_zero = [x for x in derivative if x != 0]
        num_add_enb = len(derivative_diff_zero) 
        mean_add_enb = sum(derivative_diff_zero)/num_add_enb # 6 MeanAddNumEnbs

        num_slices_with_max_enb = 0 # 1: NumSliceMaxEnbs
        num_slices_const_enb = []
        count_change = 1
        for i in range(len(enb_list)):
          if enb_list[i] == max_enb:
            num_slices_with_max_enb += 1
            
          if i > 0:
            if enb_list[i] == enb_list[i-1]:
              count_change += 1
              if i == len(enb_list)-1:
                num_slices_const_enb.append(count_change)  
            else:
              num_slices_const_enb.append(count_change)
              count_change = 1
        
        mean_slices_const_enb = sum(num_slices_const_enb)/len(num_slices_const_enb) # 2 MeanNumSliceConstEnbs

        num_slices_const_enb_diff_one = [x for x in num_slices_const_enb if x != 1]
        
        mean_slices_const_enb_diff_one = sum(num_slices_const_enb_diff_one)/len(num_slices_const_enb_diff_one) # 3 MeanNumSliceConstEnbs++1
        # Statistics:
        # 1 - NumSliceMaxEnbs: Avalia a quantidade de slices em que se manteve a máxima quantidade de eNB utilizadas no cenário considerando todos os slices.
        # 2 - MeanNumSliceConstEnbs: Avalia a média da duração de intervalos (slices) em que a quantidade de eNB ficou constante. 
        #                            Considera também duranções de 1 slice.
        # 3 - MeanNumSliceConstEnbs++1: Avalia a média da duração de intervalos (slices) em que a quantidade de eNB ficou constante. 
        #                               Considera apenas duranções maiores que 1 slice.
        # 4 - MaxAddEnbs: Avalia a quantidade máxima de eNB que foram adicionas simultaneamente
        # 5 - NumAddNumEnbs: Avalia a quantidade de adições de eNB que ocorreram no cenário.
        # 6 - MeanAddNumEnbs: Avalia a quantidade média de eNB que foram adicionadas simultaneamente
        # 7 - NumAddNumEnbsw0: Avalia a quantidade de adições de eNB que ocorreram no cenário considerando as não adições
        # 8 - MeanAddNumEnbsw0: Avalia a quantidade média de eNB que foram adicionadas simultaneamente considerando as não adições

        new_data.loc[(new_data['min_snr_used'] == min_snr) & (new_data['seed'] == seed),"NumSliceMaxEnbs"] = num_slices_with_max_enb
        new_data.loc[(new_data['min_snr_used'] == min_snr) & (new_data['seed'] == seed),"MeanNumSliceConstEnbs"] = mean_slices_const_enb
        new_data.loc[(new_data['min_snr_used'] == min_snr) & (new_data['seed'] == seed),"MeanNumSliceConstEnbs++1"] = mean_slices_const_enb_diff_one
        new_data.loc[(new_data['min_snr_used'] == min_snr) & (new_data['seed'] == seed),"MaxAddEnbs"] = max_add_enb
        new_data.loc[(new_data['min_snr_used'] == min_snr) & (new_data['seed'] == seed),"NumAddNumEnbs"] = num_add_enb
        new_data.loc[(new_data['min_snr_used'] == min_snr) & (new_data['seed'] == seed),"MeanAddNumEnbs"] = mean_add_enb
        new_data.loc[(new_data['min_snr_used'] == min_snr) & (new_data['seed'] == seed),"NumAddNumEnbsw0"] = num_add_enb/12   # 7 NumAddNumEnbsw0
        new_data.loc[(new_data['min_snr_used'] == min_snr) & (new_data['seed'] == seed),"MeanAddNumEnbsw0"] = mean_add_enb*num_add_enb/12   # 7 NumAddNumEnbsw0
    #pivot_df.reset_index(inplace=True)

  if slice_op == 'mean':
    noslice_data = new_data.groupby(id_columns, dropna = dropna).mean()
  elif slice_op == 'max':
    noslice_data = new_data.groupby(id_columns, dropna = dropna).max()
  elif slice_op == 'sum':
    noslice_data = new_data.groupby(id_columns, dropna = dropna).sum()
  elif slice_op == 'std':
    noslice_data = new_data.groupby(id_columns, dropna = dropna).std()
  else:
    print('ERRORRRRR')

  if count_enb:
    col_names = noslice_data.columns.to_list()
    for name in col_names:
      if name == col_to_keep:
        col_names.remove(name)
  
    noslice_data = noslice_data.drop(columns=col_names)#noslice_data.loc[:,col_to_keep]
  else:
    noslice_data = noslice_data.drop(columns=['Slice', 'seed'])
  # TODO: ver como ele utiliza apenas os valores da coluna NumEnbs para ter certeza que não vai dar problema na construção do gráfico
  #print(f'Unite: {noslice_data[noslice_data.isna().any(axis=1)]}, {noslice_data.isna().sum().sum()}, {noslice_data.shape}')

  return noslice_data

def compute_cov (data: pd.DataFrame, id_columns: List, enb = False):
  dropna = False

  mean_data = data.groupby(id_columns, dropna= dropna).mean()

  std_data = data.groupby(id_columns, dropna= dropna).std()

  cov_data = (std_data/mean_data)

  if enb:
    err_data = std_data#(2.228*std_data/len(std_data)*[len(data)/3])
    err_data = err_data/sqrt(len(data)/3)*stats.t.ppf(0.975, len(data)/3 - 1)# 2.228

  mean_data.columns = pd.MultiIndex.from_product([['Mean'], mean_data.columns])
  #print('Mean Data: ',mean_data.sum().sum())
  std_data.columns = pd.MultiIndex.from_product([['Std'], std_data.columns])

  cov_data.columns = pd.MultiIndex.from_product([['COV'], cov_data.columns])

  if enb:
    err_data.columns = pd.MultiIndex.from_product([['ERR'], err_data.columns])

  #print(f'Antes: {data[data==np.nan]}, {data.shape}')
  mean_data.to_csv("mean_data.csv")
  if enb:
    new_data = pd.concat([mean_data, std_data, cov_data, err_data], axis= 1).stack()  
  else:
    new_data = pd.concat([mean_data, std_data, cov_data], axis= 1).stack()
  new_data.to_csv("new_data.csv")

  new_data.index.names = new_data.index.names[:-1] + ['n_obj']

  #print(f'Mean cov: {new_data[new_data["Mean"].isna()]}, {new_data["Mean"].isna().sum()}, {new_data.shape}')
  #print(f'Zero cov: {new_data[new_data["Mean"]==0]}, {(new_data["Mean"]==0).sum()}, {new_data.shape}')
  #print(f'Sum cov: {(new_data["Mean"]==0).sum(level="min_snr_used")}')
  #print(f'Inifile: {new_data[new_data["Mean"]==0].index.get_level_values("inifile")}')
  #print(f'Inifile: {new_data[new_data["Mean"]==0].index.get_level_values(-1)}')

  #print(f'Depois: {new_data[new_data.isna().any(axis=1)]}, {new_data.shape}')
  #print(f'Depois: {new_data[new_data["Std"].isna()]}, {new_data.shape}')

  return new_data
  #return new_data.reset_index(new_data.index.nlevels-1)

def getCOV(data: pd.DataFrame, extra_info: pd.DataFrame, ues_per_slice: dict, nonactive_ues: pd.DataFrame, id_columns: list = ['Inter', 'RBs', 'min_snr_used', 'repetition', 'inifile'],
           unite: bool = True, slice_op: str= 'mean', count_enb: bool = False, enb = False, col_to_keep = "NumEnbs"):

  #print(f'\nUes por slice: {ues_per_slice}\n')
  #print(f'\nData index: {data.index}\n\n')
  #print(f'\nData columns: {data.columns}\n\n')
  #print(f'Data: {data}')
  tmp: pd.DataFrame
  
  if unite:
    #print(f'\nAntes Unite: {data[data==np.nan]}, {data.shape}')
    if count_enb:
      tmp = unite_slices(processed_data=data, id_columns=id_columns, extra_info=extra_info, slice_op=slice_op, nonactive_ues=nonactive_ues, ues_per_slice=ues_per_slice, count_enb=True, col_to_keep=col_to_keep)
    else:
      tmp = unite_slices(processed_data=data, id_columns=id_columns, extra_info=extra_info, slice_op=slice_op, nonactive_ues=nonactive_ues, ues_per_slice=ues_per_slice)
    #print(f'\nDepois Unite: {tmp[tmp==np.nan]}, {tmp.shape}')
  else:
    tmp = pd.concat([data, extra_info[id_columns]], axis= 1)

  #print('Before cov: ', tmp)
  cov_columns = []
  for col in id_columns:
    if 'repetition' == col:
      continue
    if count_enb and 'inifile' == col:
      continue
    cov_columns.append(col)

  new_data = compute_cov(tmp, id_columns=cov_columns, enb=count_enb)

  #print('Data: ', new_data.sum().sum())
  #print('Shape: ',new_data.shape)

  return new_data

def processInitialData(initial_data):

  initial_data = initial_data.replace(('?'),np.NaN)

  #runs = dataInfo['run'].unique()

  modules = initial_data["module"].unique()

  itervar = initial_data[initial_data['type'] == "itervar"]
  runattr = initial_data[initial_data['type'] == "runattr"]
  param = initial_data[initial_data['type'] == "param"]
  scalar = initial_data[initial_data['type'] == "scalar"]
  vector = initial_data[initial_data['type'] == "vector"]
  attr = initial_data[initial_data['type'] == "attr"]

  infoNameAttr = initial_data["type"].unique()

  repetitions = int(runattr[runattr["attrname"] == 'repetition']["attrvalue"].max()) + 1 #Número de repetições feitas

  """Itervar processing"""
  preItervar = itervar.pivot(index='run', columns='attrname', values='attrvalue').astype({"sched": object})
  num_enbs = pd.DataFrame()
  num_enbs["NumEnbs"] = preItervar["NumEnbs"].astype({"NumEnbs": float})

  """Runattr processing"""
  preRunattr = runattr.pivot(index='run', columns='attrname', values='attrvalue').astype({"repetition": int})

  """Vector data pre-processing"""
  preVector = vector[vector.module != "_runattrs_"]

  """Scalar data pre-processing"""
  preScalar = scalar[scalar.module != "_runattrs_"]
  #.sctp with duplicated entries (?) than removed
  preScalar = preScalar[~preScalar["module"].str.endswith("sctp")]
  preData = preScalar.assign(qname = preScalar.module + '.' + preScalar.name)
  newData = preData.pivot(index='run', columns='qname', values='value')

  extra_info = preItervar.assign(min_snr_used = newData.index.str.split('_').str[3].str.findall(r'\d+').str[0], repetition = preRunattr['repetition'], inifile = preRunattr['inifile'])

  return preItervar, preRunattr, preVector, preScalar, extra_info, num_enbs

def get_data_vector_mean(data: pd.DataFrame, operation= np.mean):
  data = data.applymap(lambda x: operation(list(map(float, x.split()))), na_action= 'ignore')
  return data

#Considera que acha um unico valor para uma combinação de seed, slice, ue e min_snr_used
def get_nonactiveapp_ues(data_packets_sent: pd.DataFrame, extra_info: pd.DataFrame):

  user_app_status = {}
  seeds = []
  ues_numbers = []

  for name in data_packets_sent.index:
    p = re.compile(r'seed_\d+')
    m = p.search(name)
    if m:
      numbers = re.compile(r'\d+')
      seed = numbers.search(m.group())
      seeds.append(int(seed.group()))
    else:
      print('ERROR: Não foi possível determinar a seed.')

  for s in data_packets_sent.columns:
    p = re.compile(r'\d+')
    m = p.search(s)
    if m:
      ues_numbers.append(int(m.group()))
    else:
      print('ERROR: Não foi possível determinar o número do UE.')

  tmp_data_1: pd.DataFrame = data_packets_sent.assign(**{"Slice": extra_info['Slice'].astype(int), "Seed": seeds, "MinSnr": extra_info['min_snr_used'].astype(int)})
  result = tmp_data_1.set_index(["Seed", "Slice", "MinSnr", tmp_data_1.index]).sort_index() == 0
  result.columns = np.array(ues_numbers) - min(ues_numbers)

  #print(result)
  #print(result.loc[(3, 1, 10), 182])

  return result

def compare_csvs_video(csvs_info: List[list], dict_ids: dict, ues_per_slice: dict, extra: bool= False, only_enb_data: bool = False, enb_data: str = "NumEnbs", slice_op: str = "mean"):

  results_throughput = []
  results_enb = []
  results_enb_hist = []
  results_sinr = []
  results_rcvd_packets = []
  results_packets_sent = []
  results_enddelay = []
  value_keys = []

  id_columns = ['Inter', 'RBs', 'min_snr_used', 'repetition', 'inifile']#TODO: do this better according to inputs

  count = 0
  for mode in csvs_info:
    print("mode: ", mode)
    csv_df = pd.DataFrame()
    for csv in csvs_info[mode]:
      chosen_seed = csv['seed']
      csv_path = csv['path']
      new_data_frame = pd.read_csv(csv_path)
      new_data_frame['run'] = new_data_frame['run'].astype(str) + f'_seed_{chosen_seed}'
      csv_df = pd.concat([csv_df, new_data_frame])

    preItervar, preRunattr, preVector, preScalar, extra_info, num_enbs = processInitialData(csv_df)


    data_packets_sent = get_data_from_scalar("packetSent:count", "server", preScalar)
    nonactive_ues = get_nonactiveapp_ues(data_packets_sent, extra_info)
    
    if not only_enb_data:
      print('Getting throughput.')
      #print(f'\Vector: {preVector[preVector==np.nan]}, {preVector.shape}')
      tmp_throughput = get_data_from_vector('throughput:vector', "ue", preVector)['vecvalue']
      data_throughput = get_data_vector_mean(tmp_throughput)
      throughput = getCOV(data=data_throughput.fillna(0), extra_info=extra_info, id_columns=id_columns, unite= True, nonactive_ues= nonactive_ues, ues_per_slice=ues_per_slice)
      #pd.set_option('display.max_columns', None)  # or 1000
      #pd.set_option('display.max_rows', None)  # or 1000
      #pd.set_option('display.max_colwidth', None)  # or 199
      #print('Zeroes: ', throughput[throughput['Mean'] == 0].index.to_series())
      
      print('Getting eNBs.') # Usando o maximo em vez da media: media de maximos
      enbs = getCOV(data=num_enbs, extra_info=extra_info, id_columns=id_columns, unite= True, nonactive_ues= nonactive_ues, count_enb=True, ues_per_slice=ues_per_slice,slice_op="mean", col_to_keep="NumEnbs")
      hist_enbs = unite_slices(processed_data=num_enbs, extra_info=extra_info, id_columns=id_columns, slice_op= 'mean', nonactive_ues= nonactive_ues, ues_per_slice=ues_per_slice)
      #print(f'\nColumns: {enbs.columns}\nObj: {enbs.index.get_level_values("n_obj")}\nInifile: {enbs.index.get_level_values("inifile")}\n')

      print('Getting SINR.')
      data_sinr = get_data_from_scalar("rcvdSinr:mean", "ue", preScalar)
      sinr = getCOV(data=data_sinr.fillna(-10), extra_info=extra_info, id_columns=id_columns, unite= True, nonactive_ues= nonactive_ues, ues_per_slice=ues_per_slice)


      results_throughput.append(throughput)
      results_enb.append(enbs)
      results_enb_hist.append(hist_enbs)
      results_sinr.append(sinr)

      if extra:
        tmp_enddelay = get_data_from_vector('endToEndDelay:vector', "ue", preVector)['vecvalue']
        data_enddelay = get_data_vector_mean(tmp_enddelay)
        enddelay = getCOV(data=data_enddelay, extra_info=extra_info, id_columns=id_columns, unite= True, nonactive_ues= nonactive_ues, ues_per_slice=ues_per_slice)

        results_enddelay.append(enddelay)

        data_rcvd_packets = get_data_from_scalar("packetReceived:count", "ue", preScalar)
        rcvd_packets, _, _ = getCOV(data=data_rcvd_packets, extra_info=extra_info, id_columns=id_columns, unite= True, slice_op= 'sum', nonactive_ues= nonactive_ues, ues_per_slice=ues_per_slice)

        results_rcvd_packets.append(rcvd_packets)

        packets_sent, _, _ = getCOV(data=data_packets_sent, extra_info=extra_info, id_columns=id_columns, unite= True, slice_op= 'sum', nonactive_ues= nonactive_ues, ues_per_slice=ues_per_slice)

        results_packets_sent.append(packets_sent)

      tmp_tuple = ()
      for name in dict_ids:
        tmp_tuple += (dict_ids[name][count],)

      value_keys.append(tmp_tuple)

      count += 1
    
    else:
      print('Getting eNBs: ' + enb_data)  #sempre observando a media: media de medias
      if enb_data == "NumEnbs":
        slice_op = "max"

      if mode == "ga":
        k = 100
      enbs = getCOV(data=num_enbs, extra_info=extra_info, id_columns=id_columns, unite= True, nonactive_ues= nonactive_ues, count_enb=True, ues_per_slice=ues_per_slice,slice_op=slice_op, col_to_keep=enb_data)
      hist_enbs = unite_slices(processed_data=num_enbs, extra_info=extra_info, id_columns=id_columns, slice_op= slice_op, nonactive_ues= nonactive_ues, ues_per_slice=ues_per_slice)
      results_enb.append(enbs)
      results_enb_hist.append(hist_enbs)

      tmp_tuple = ()
      for name in dict_ids:
        tmp_tuple += (dict_ids[name][count],)

      value_keys.append(tmp_tuple)

      count += 1
      slice_op = "mean"

  names = dict_ids.keys()

  if not only_enb_data:
    all_throughput = pd.concat(results_throughput, keys= value_keys, names= names)
    #print(f'Inside func: {(all_throughput["Mean"] == 0).sum()}/{len(all_throughput["Mean"])}')
    #print((all_throughput["Mean"] == 0)[(all_throughput["Mean"] == 0) == True])
    all_sinr = pd.concat(results_sinr, keys= value_keys, names= names)
    all_enb = pd.concat(results_enb, keys= value_keys, names= names)
    all_enb_hist = pd.concat(results_enb_hist, keys= value_keys, names= names)
    #all_enb = pd.DataFrame({'Mean': all_enb_mean['Mean'], 'Std': all_enb_std['Mean']})
    #all_enb = all_enb_mean

    #print(all_throughput.index)

    if extra:
      all_enddelay = pd.concat(results_enddelay, keys= value_keys, names= names)
      all_rcvd_packets = pd.concat(results_rcvd_packets, keys= value_keys, names= names)
      all_packets_sent = pd.concat(results_packets_sent, keys= value_keys, names= names)
      return all_throughput, all_sinr, all_enb, all_enb_hist, all_enddelay, all_rcvd_packets, all_packets_sent
    else:
      return all_throughput, all_sinr, all_enb, all_enb_hist
  
  else:
    all_enb = pd.concat(results_enb, keys= value_keys, names= names)
    all_enb_hist = pd.concat(results_enb_hist, keys= value_keys, names= names)

    return all_enb, all_enb_hist

def propagate_std(data, id):

  num_options = len(list(data.index.get_level_values(id).unique()))

  gp_ids = list(data.index.names)
  gp_ids.remove(id)

  new_std = np.sqrt((data['Std']**2).groupby(gp_ids).sum())/num_options

  new_mean = data['Mean'].groupby(gp_ids).mean()

  return pd.DataFrame({'Mean': new_mean, 'Std': new_std})

def process_csv(filename, app='video'):
  
  initialData = pd.read_csv(filename)
  num_ues = 60
  directions = 2

  preItervar, preRunattr, preVector, preScalar, extra_info, num_enbs = processInitialData(initialData)

  """# **Analisando resultados**"""
  if app == 'video':
  ## **Video Metrics**
  ### Throughput

    tmp_throughput_ul = get_data_from_vector('throughput:vector', "server", preVector, num_ues, 1)['vecvalue']
    data_throughput_ul = get_data_vector_mean(tmp_throughput_ul)

    throughput_ul, colors, names = getCOV(data_throughput_ul, extra_info, 'min_snr_used', unite= True, preRunattr = preRunattr)

    lines = throughput_ul.index.get_level_values("RBs").tolist()

    fig = px.ecdf(throughput_ul, x="Mean", color=colors, labels= {"Mean": "Throughput (bps)", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: UE Throughput UL - CDF", hover_data = ["COV"], ecdfmode="reversed", hover_name = names, line_dash= lines, category_orders={"color": ["5", "10", "15"]})

    fig.show()

    tmp_throughput_dl = get_data_from_vector('throughput:vector', "ue", preVector, num_ues, 1)['vecvalue']
    data_throughput_dl = get_data_vector_mean(tmp_throughput_dl)

    throughput_dl, colors, names = getCOV(data_throughput_dl, extra_info, 'min_snr_used', unite= True, preRunattr = preRunattr)

    lines = throughput_dl.index.get_level_values("RBs").tolist()

    fig = px.ecdf(throughput_dl, x="Mean", color=colors, labels= {"Mean": "Throughput (bps)", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: UE Throughput DL - CDF", hover_data = ["COV"], hover_name = names, ecdfmode="reversed", line_dash= lines, category_orders={"color": ["5", "10", "15"]})

    fig.show()

    fig = px.ecdf(throughput_dl, x="COV", color=colors, labels= {"Mean": "Throughput (bps)", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: COV UE Throughput DL - CDF", hover_data = ["COV"], hover_name = names, ecdfmode="reversed", line_dash= lines, category_orders={"color": ["5", "10", "15"]})

    fig.show()

    enbs, colors, names = getCOV(num_enbs, extra_info, 'min_snr_used', unite= True, preRunattr = preRunattr)
    enbs_std, colors, names = getCOV(num_enbs, extra_info, 'min_snr_used', unite= True, slice_op='std', preRunattr = preRunattr)

    fig = px.bar(enbs, x= colors, y= "Mean", color= colors, labels= {"x" : "Min Snr Used (dB)" ,"color" : "Min Snr Used (dB)", "y": "Mean of Used Enbs"},
                title= "SLICED: Num Enbs Throughput DL - CDF", hover_name = names, error_y = enbs_std["Mean"])
    fig.show()

    """### End To End Delay"""

    tmp_enddelay_dl = get_data_from_vector('endToEndDelay:vector', "ue", preVector, num_ues, 1)['vecvalue']
    data_enddelay_dl = get_data_vector_mean(tmp_enddelay_dl)

    enddelay_dl, colors, names = getCOV(data_enddelay_dl, extra_info, 'min_snr_used', unite= True, preRunattr = preRunattr)

    lines = enddelay_dl.index.get_level_values("RBs").tolist()

    fig = px.ecdf(enddelay_dl, x="Mean", color=colors, labels= {"Mean": "Delay (s)", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: UE End to End Delay DL - CDF", hover_data = ["COV"], hover_name = names, ecdfmode="reversed", line_dash= lines)

    fig.show()

    tmp_enddelay_ul = get_data_from_vector('endToEndDelay:vector', "server", preVector, num_ues, 1)['vecvalue']
    data_enddelay_ul = get_data_vector_mean(tmp_enddelay_ul)

    enddelay_ul, colors, names = getCOV(data_enddelay_ul, extra_info, 'min_snr_used', unite= True, preRunattr = preRunattr)

    lines = enddelay_ul.index.get_level_values("RBs").tolist()

    fig = px.ecdf(enddelay_ul, x="Mean", color=colors, labels= {"Mean": "Delay (s)", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: UE End to End Delay UL - CDF", hover_data = ["COV"], hover_name = names, ecdfmode="reversed", line_dash= lines)

    fig.show()

    """### Packets"""

    data_packets_rcvd_ul = get_data_from_scalar("packetReceived:count", "server", preScalar, num_ues, 1)

    ul_packets_rcvd, colors, names = getCOV(data_packets_rcvd_ul, extra_info, 'min_snr_used', unite= True, slice_op= 'sum', preRunattr = preRunattr)

    lines = ul_packets_rcvd.index.get_level_values("RBs").tolist()

    fig = px.ecdf(ul_packets_rcvd, x="Mean", color=colors, labels= {"Mean": "Packets", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: UE Packets Received UL - CDF", hover_data = ["COV"], hover_name = names,ecdfmode="reversed", line_dash= lines)

    fig.show()

    data_packets_rcvd_ul.isna().sum().sum()

    data_packets_sent_ul = get_data_from_scalar("packetSent:count", "ue", preScalar, num_ues, 1)

    ul_packets_sent, colors, names = getCOV(data_packets_sent_ul, extra_info, 'min_snr_used', unite= True, slice_op= 'sum', preRunattr = preRunattr)

    lines = ul_packets_sent.index.get_level_values("RBs").tolist()

    fig = px.ecdf(ul_packets_sent, x="Mean", color=colors, labels= {"Mean": "Packets", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: Packets Sent per UE UL - CDF", hover_data = ["COV"], hover_name = names,ecdfmode="reversed", line_dash= lines)

    fig.show()

    data_packets_sent_ul.isna().sum().sum()

    data_packets_dl = get_data_from_scalar("packetReceived:count", "ue", preScalar, num_ues, 1)

    dl_packets, colors, names = getCOV(data_packets_dl, extra_info, 'min_snr_used', unite= True, slice_op= 'sum', preRunattr = preRunattr)

    lines = dl_packets.index.get_level_values("RBs").tolist()

    fig = px.ecdf(dl_packets, x="Mean", color=colors, labels= {"Mean": "Packets", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: Packets Received per UE DL - CDF", hover_data = ["COV"], hover_name = names,ecdfmode="reversed", line_dash= lines)

    fig.show()

    data_packets_dl.isna().sum().sum()

    data_packets_sent_dl = get_data_from_scalar("packetSent:count", "server", preScalar, num_ues, 1)

    dl_packets_sent, colors, names = getCOV(data_packets_sent_dl, extra_info, 'min_snr_used', unite= True, slice_op= 'sum', preRunattr = preRunattr)

    lines = dl_packets_sent.index.get_level_values("RBs").tolist()

    fig = px.ecdf(dl_packets_sent, x="Mean", color=colors, labels= {"Mean": "Packets", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: Packets Sent per UE DL - CDF", hover_data = ["COV"], hover_name = names,ecdfmode="reversed", line_dash= lines)

    fig.show()

    data_packets_sent_dl.isna().sum().sum()

    """### PacketsBytes"""

    data_packets_rcvd_ul = get_data_from_scalar("packetReceived:sum(packetBytes)", "server", preScalar, num_ues, 1)

    ul_packets_rcvd, colors, names = getCOV(data_packets_rcvd_ul, extra_info, 'min_snr_used', unite= True, slice_op= 'sum', preRunattr = preRunattr)

    lines = ul_packets_rcvd.index.get_level_values("RBs").tolist()

    fig = px.ecdf(ul_packets_rcvd, x="Mean", color=colors, labels= {"Mean": "Bytes", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: UE Bytes Received UL - CDF", hover_data = ["COV"], hover_name = names,ecdfmode="reversed", line_dash= lines)

    fig.show()

    data_packets_rcvd_ul.isna().sum().sum()

    data_packets_sent_ul = get_data_from_scalar("packetSent:sum(packetBytes)", "ue", preScalar, num_ues, 1)

    ul_packets_sent, colors, names = getCOV(data_packets_sent_ul, extra_info, 'min_snr_used', unite= True, slice_op= 'sum', preRunattr = preRunattr)

    lines = ul_packets_sent.index.get_level_values("RBs").tolist()

    fig = px.ecdf(ul_packets_sent, x="Mean", color=colors, labels= {"Mean": "Bytes", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: Bytes Sent per UE UL - CDF", hover_data = ["COV"], hover_name = names,ecdfmode="reversed", line_dash= lines)

    fig.show()

    data_packets_sent_ul.isna().sum().sum()

    data_packets_dl = get_data_from_scalar("packetReceived:sum(packetBytes)", "ue", preScalar, num_ues, 1)

    dl_packets, colors, names = getCOV(data_packets_dl, extra_info, 'min_snr_used', unite= True, slice_op= 'sum', preRunattr = preRunattr)

    lines = dl_packets.index.get_level_values("RBs").tolist()

    fig = px.ecdf(dl_packets, x="Mean", color=colors, labels= {"Mean": "Bytes", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: Bytes Received per UE DL - CDF", hover_data = ["COV"], hover_name = names,ecdfmode="reversed", line_dash= lines)

    fig.show()

    data_packets_dl.isna().sum().sum()

    data_packets_sent_dl = get_data_from_scalar("packetSent:sum(packetBytes)", "server", preScalar, num_ues, 1)

    dl_packets_sent, colors, names = getCOV(data_packets_sent_dl, extra_info, 'min_snr_used', unite= True, slice_op= 'sum', preRunattr = preRunattr)

    lines = dl_packets_sent.index.get_level_values("RBs").tolist()

    fig = px.ecdf(dl_packets_sent, x="Mean", color=colors, labels= {"Mean": "Bytes", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: Bytes Sent per UE DL - CDF", hover_data = ["COV"], hover_name = names,ecdfmode="reversed", line_dash= lines)

    fig.show()

    data_packets_sent_dl.isna().sum().sum()

    """## **General 3GPP Metrics**

    #### **Sinr recebido pelos UEs**
    """

    data_sinr = get_data_from_scalar("rcvdSinr:mean", "ue", preScalar, num_ues, 1)

    data_sinr.isna().sum().sum()

    mean_sinr_dl, colors, names = getCOV(data_sinr.fillna(0), extra_info, 'min_snr_used', preRunattr = preRunattr)

    lines = mean_sinr_dl.index.get_level_values("RBs").tolist()

    fig = px.ecdf(mean_sinr_dl, x="Mean", color=colors, labels= {"Mean": "Sinr:Mean (dB)", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: Downlink Sinr per UE - CDF", hover_data = ["COV"], ecdfmode="reversed", hover_name = names, line_dash = lines)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE SNR - VER COMO CONSIDERAR

    fig = px.ecdf(mean_sinr_dl, x="COV", color=colors, labels= {"Mean": "Sinr:Mean (dB)", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: Downlink Sinr COV per UE - CDF", hover_data = ["Mean"], hover_name = names, line_dash= lines, category_orders={"color": ["5", "10", "15"]})
    fig.update_layout(
    legend=dict(
        #orientation="h",  # Define a orientação horizontal da legenda
        x=0.5,  # Define a posição horizontal da legenda (0-1)
        y=-0.2,  # Define a posição vertical da legenda (<0 move a legenda para baixo)
        #traceorder="normal",  # Define a ordem em que as legendas são exibidas
        #font=dict(size=10),  # Define o tamanho da fonte da legenda
        #bgcolor="rgba(0,0,0,0)",  # Define a cor de fundo da legenda (transparente)
    )
)
    fig.show()

    """Sinr: aumentou a largura de banda"""

    mean_sinr_dl, colors, names = getCOV(data_sinr, extra_info, 'min_snr_used', preRunattr = preRunattr)

    dl_thr, colors, names = getCOV(data_throughput_dl, extra_info, 'min_snr_used', dropna = True, preRunattr = preRunattr)

    facet = mean_sinr_dl.index.get_level_values("RBs").tolist()

    bandw = mean_sinr_dl.index.get_level_values("RBs").to_series(index = dl_thr.index).map(lambda x: int(x)*10**6/5)

    s_ef = dl_thr["Mean"] * 8 / (bandw / num_ues)

    fig = px.scatter(x= mean_sinr_dl['Mean'], y= s_ef, color = colors, labels= {"x": "SINR (dB)", "y": "Spectral Efficiency [bits/s/Hz]", "color": "", "facet_col": "RBs"},
                  title= "SLICED: Spectral Efficiency DL per UE - CDF", hover_name = names, facet_col= facet)

    fig.show()

    """#### **Sinr enviado pelos UEs**"""

    idRcvdSinr = preVector["vecvalue"].filter(regex=("idRcvdSinr:vector$")).fillna('')
    rcvdSinr = preVector["vecvalue"].filter(regex=("rcvdSinr:vector$")).fillna('')

    if rcvdSinr.size != idRcvdSinr.size:
      print("ERROR")

    mean_rcvdsinr = pd.DataFrame(index = idRcvdSinr.index, columns = range(num_ues)).fillna(0)
    counter = pd.DataFrame(index = idRcvdSinr.index, columns = range(num_ues)).fillna(0)

    for c in range(len(rcvdSinr.columns)):
      for i in range(len(rcvdSinr.index)):
        rcvdSinrList = rcvdSinr.iloc[i, c].split()
        idList = idRcvdSinr.iloc[i, c].split()
        if len(rcvdSinrList) != len(idList):
          print("ERROR")
        for j in range(len(rcvdSinrList)):
          mean_rcvdsinr.iloc[i, int(idList[j])] += float(rcvdSinrList[j])
          counter.iloc[i, int(idList[j])] += 1

    mean_rcvdsinr = mean_rcvdsinr/counter

    mean_sinr_ul, colors, names = getCOV(mean_rcvdsinr, extra_info, 'min_snr_used', preRunattr = preRunattr)

    fig = px.ecdf(mean_sinr_ul, x="Mean", color=colors, labels= {"Mean": "Sinr:Mean (dB)", "color" : "Min Snr Used (dB) (dBm)"}, markers= False, lines= True,
                  title= "SLICED: Uplink Sinr per UE - CDF", hover_data = ["COV"], ecdfmode="reversed", hover_name = names)

    fig.show()

    fig = px.ecdf(mean_sinr_ul, x="COV", color=colors, labels= {"Mean": "Sinr:Mean (dB)", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Uplink Sinr COV per UE - CDF", hover_data = ["Mean"], hover_name = names)

    fig.show()

    data_ul_sinr = get_data_from_scalar("rcvdSinr:mean", "ue", preScalar, num_ues, 1)

    sinr = gen_ues_data_single(data_sinr, num_ues, directions)

  elif app == 'voip':
    ## **VoIP**
    #### Throughput Calculation

    dataUL = get_data_from_scalar("voIPReceivedThroughput:mean", "server", preScalar, num_ues, 1)
    dataDL = get_data_from_scalar("voIPReceivedThroughput:mean", "ue", preScalar, num_ues, 1)
    #dataUL = dataUL.fillna(0)
    #dataDL = dataDL.fillna(0)

    #plotData = newData.assign(nan_percentageUL = nan_percentageUL)
    #plotData = plotData.assign(nan_percentageDL = nan_percentageDL)
    plotData = preVector.assign(repetition = preRunattr["repetition"])

    throughputs = pd.DataFrame()

    #Throughput DL
    for a in dataDL.columns:
      p = re.findall(r'\d+', a)
      i = [int(s) for s in p] #Acha dois numeros

      throughputs["Throughput ue" + str(i[0])] = dataDL[a]


    #Throughput UL
    for b in dataUL.columns:
      p = re.findall(r'\d+', b)
      i = [int(s) for s in p]

      #If there was multiple ue groups
      if len(i) > 0:
        group = int(i[0]/(num_ues*directions))
        id = i[0] % (num_ues*directions)

        throughputs["Throughput ue" + str(i[0])] += dataUL[b]


    throughputSum = dataDL.sum(axis=1).add(dataUL.sum(axis=1))

    #throughput = throughput*8/(10**6)
    nan_count = throughputs.isnull().sum(axis=1)
    nan_percentage = nan_count / num_ues * 100

    dataDLUL = pd.concat([throughputs, plotData], axis= 1)
    dataDLUL = dataDLUL.assign(throughput_mean = throughputSum / num_ues, nan_percentage = nan_percentage)

    """#### **NaN Results**"""

    tmp_data, colors, names = getCOV(dataUL.isna()*100, extra_info, "min_snr_used" , preRunattr = preRunattr)

    tmp_data = tmp_data.replace(0, np.nan).dropna()

    colors = tmp_data.index.get_level_values('min_snr_used').tolist()

    names = tmp_data.index.get_level_values('n_obj').tolist()

    fig = px.bar(tmp_data, x=names, y="Mean", hover_name = names, barmode= "group",
                color=colors, labels= {"Mean": "Percentage of Slices (%)", "x": "Apps", "color": "Min Snr Used (dB)"},
                title= "SLICED: Percentage of times that each UE couldn't connect (UL Throughput)")

    fig.show()

    #CHANGE

    """#### **Throughput results**"""

    ul_thr, colors, names = getCOV(dataUL.fillna(0), extra_info, 'min_snr_used', dropna= True, preRunattr = preRunattr)

    fig = px.ecdf(ul_thr, x='Mean', color = colors, labels= {"Mean": "Throughput:Mean (Bps)", "color": "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Throughput UL per UE - CDF", ecdfmode="reversed", hover_name = names)

    fig.show()

    dl_thr, colors, names = getCOV(dataDL, extra_info, 'min_snr_used', dropna= True, preRunattr = preRunattr)

    fig = px.ecdf(dl_thr, x='Mean', color = colors, labels= {"Mean": "Throughput:Mean (Bps)", "color": "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Throughput DL per UE - CDF", ecdfmode="reversed", hover_name = names)

    fig.show()

    fig = px.ecdf(dl_thr, x='COV', color = colors, labels= {"Mean": "Throughput:Mean (Bps)", "color": "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: COV Throughput DL per UE - CDF", hover_name = names, hover_data= ["Mean"])

    fig.show()

    """#### **Spectral Eficiency**"""

    #Efic Spec = throughput / (bandw * %utilization)

    bandw = 20*10**6

    mean_sinr_dl, colors, names = getCOV(data_sinr, extra_info, 'min_snr_used', preRunattr = preRunattr)

    dl_thr, colors, names = getCOV(dataDL, extra_info, 'min_snr_used', dropna= True, preRunattr = preRunattr)

    s_ef = dl_thr * 8 / (bandw / num_ues)

    fig = px.scatter(x= mean_sinr_dl['Mean'], y= s_ef['Mean'], color = colors, labels= {"x": "SINR (dB)", "y": "Spectral Efficiency [bits/s/Hz]", "color": "Min Snr Used (dB)"},
                  title= "SLICED: Spectral Efficiency DL per UE - CDF", hover_name = names)

    fig.show()

    """### **Comparando métricas VoIP**

    #### Delay
    """

    data_delay_ul = get_data_from_scalar("voIPPlayoutDelay", "server", preScalar, num_ues, 1)
    data_delay_dl= get_data_from_scalar("voIPPlayoutDelay", "ue", preScalar, num_ues, 1)

    data_frame_delay_ul = get_data_from_scalar("voIPFrameDelay", "server", preScalar, num_ues, 1)/100
    data_frame_delay_dl = get_data_from_scalar("voIPFrameDelay", "ue", preScalar, num_ues, 1)/100

    delay_plot, delay = gen_ues_data(data_delay_ul, data_delay_dl, 0.1, num_ues, num_ues, directions, plotData)

    """#### Loss"""

    data_frameloss_ul = get_data_from_scalar("voIPFrameLoss", "server", preScalar, num_ues, 1)/100
    data_frameloss_dl = get_data_from_scalar("voIPFrameLoss", "ue", preScalar, num_ues, 1)/100

    data_playloss_ul = get_data_from_scalar("voIPPlayoutLoss", "server", preScalar, num_ues, 1)/100
    data_playloss_dl = get_data_from_scalar("voIPPlayoutLoss", "ue", preScalar, num_ues, 1)/100

    data_tailloss_ul = get_data_from_scalar("voIPTaildropLoss", "server", preScalar, num_ues, 1)/100
    data_tailloss_dl = get_data_from_scalar("voIPTaildropLoss", "ue", preScalar, num_ues, 1)/100

    new_data_frameloss_ul = gen_ues_data_single(data_frameloss_ul, num_ues, directions)
    new_data_frameloss_dl = gen_ues_data_single(data_frameloss_dl, num_ues, directions)

    new_data_playloss_ul = gen_ues_data_single(data_playloss_ul, num_ues, directions)
    new_data_playloss_dl = gen_ues_data_single(data_playloss_dl, num_ues, directions)

    new_data_tailloss_ul = gen_ues_data_single(data_tailloss_ul, num_ues, directions)
    new_data_tailloss_dl = gen_ues_data_single(data_tailloss_dl, num_ues, directions)

    data_loss_ul = new_data_frameloss_ul + new_data_playloss_ul + new_data_tailloss_ul
    data_loss_dl = new_data_frameloss_dl + new_data_playloss_dl + new_data_tailloss_dl

    frameloss_plot, frameloss = gen_ues_data(data_frameloss_ul, data_frameloss_dl, 0.01, num_ues, num_ues, directions, plotData)
    playloss_plot, playloss = gen_ues_data(data_playloss_ul, data_playloss_dl, 0.01, num_ues, num_ues, directions, plotData)
    tailloss_plot, tailloss = gen_ues_data(data_tailloss_ul, data_tailloss_dl, 0.01, num_ues, num_ues, directions, plotData)

    loss = frameloss + playloss + tailloss

    loss_plot = pd.concat([loss, plotData], axis= 1)

    """#### Jitter"""

    data_jitter_ul = get_data_from_scalar("voIPJitter", "server", preScalar, num_ues, 1)
    data_jitter_dl = get_data_from_scalar("voIPJitter", "ue", preScalar, num_ues, 1)

    jitter_plot, jitter = gen_ues_data(data_jitter_ul, data_jitter_dl, 0.4, num_ues, num_ues, directions, plotData)

    jitter_stacked = jitter.stack(dropna= False).fillna(0)
    delay_stacked = delay.stack(dropna = False)
    delay_isna = delay_stacked.isna()

    for i in range(jitter_stacked.size):
      if delay_isna.iloc[i]: jitter_stacked.iloc[i] = np.NaN

    jitter_unstacked = jitter_stacked.unstack(level=[-1])
    nan_count = jitter_unstacked.isnull().sum(axis=1)
    nan_percentage = nan_count / num_ues * 100

    new_jitter_plot = pd.concat([jitter_unstacked, plotData], axis= 1)
    new_jitter_plot = new_jitter_plot.assign(nan_count = nan_count, nan_percentage = nan_percentage)

    """#### MOS"""

    data_mos_ul = get_data_from_scalar("voIPMos", "server", preScalar, num_ues, 1)
    data_mos_dl = get_data_from_scalar("voIPMos", "ue", preScalar, num_ues, 1)

    mos_plot, mos = gen_ues_data(data_mos_ul, data_mos_dl, 0, num_ues, num_ues, directions, plotData)

    """#### **Results**

    **PlayoutDelay: < 0.1s**

    PlayoutDelay => max_jitter

    Obs:
    1.   FrameDelay = ArrivalTime - PayloadTimestamp
    """

    dl_framedelay, colors, names = getCOV(data_frame_delay_dl, extra_info, 'min_snr_used', preRunattr = preRunattr)

    fig = px.ecdf(dl_framedelay, x="Mean", color=colors, labels= {"Mean": "Delay: Mean (s)", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Frame Delay DL per UE - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ul_framedelay, colors, names = getCOV(data_frame_delay_ul, extra_info, 'min_snr_used', preRunattr = preRunattr)

    fig = px.ecdf(ul_framedelay, x="Mean", color=colors, labels= {"Mean": "Delay: Mean (s)", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Frame Delay UL per UE - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    dl_delay, colors, names = getCOV(data_delay_dl, extra_info, 'min_snr_used', preRunattr = preRunattr)

    fig = px.ecdf(dl_delay, x="Mean", color=colors, labels= {"Mean": "Delay: Mean (s)", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Playout Delay DL per UE - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE TEMPO - VER COMO CONSIDERAR

    ul_delay, colors, names = getCOV(data_delay_ul, extra_info, 'min_snr_used', preRunattr = preRunattr)

    fig = px.ecdf(ul_delay, x="Mean", color=colors, labels= {"Mean": "Delay: Mean (s)", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Playout Delay UL per UE - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE TEMPO - VER COMO CONSIDERAR

    mean_delay, colors, names = getCOV(delay, extra_info, 'min_snr_used', preRunattr = preRunattr)

    fig = px.ecdf(mean_delay, x="Mean", color=colors, labels= {"Mean": "Delay (s)", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  marginal="rug",  title= "SLICED: Playout Delay per UE - CDF", hover_data = ["COV"], hover_name = names)

    #fig.show()

    """**Loss < 1%** 

    Considering: 

    1. Playout Loss => Times jitter > 0

    2. Tail Drop Loss => buffer full

    3. Frame Loss => Channel Loss

    """

    ul_loss, colors, names = getCOV(data_loss_ul, extra_info, 'min_snr_used', preRunattr = preRunattr)

    fig = px.ecdf(ul_loss, x="Mean", color=colors, labels= {"Mean": "Loss rate", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Loss per UE UL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE TEMPO E PERDAS - VER COMO CONSIDERAR

    dl_loss, colors, names = getCOV(data_loss_dl, extra_info, 'min_snr_used', preRunattr = preRunattr)

    fig = px.ecdf(dl_loss, x="Mean", color=colors, labels= {"Mean": "Loss rate", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Loss per UE DL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE TEMPO E PERDAS - VER COMO CONSIDERAR

    ul_frame_loss, colors, names = getCOV(data_frameloss_ul, extra_info, 'min_snr_used', preRunattr = preRunattr)

    fig = px.ecdf(ul_frame_loss, x="Mean", color=colors, labels= {"Mean": "Loss rate", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Frame Loss per UE UL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE TEMPO E PERDAS - VER COMO CONSIDERAR

    dl_frame_loss, colors, names = getCOV(data_frameloss_dl, extra_info, 'min_snr_used', preRunattr = preRunattr)

    fig = px.ecdf(dl_frame_loss, x="Mean", color=colors, labels= {"Mean": "Loss rate", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Frame Loss per UE DL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE TEMPO E PERDAS - VER COMO CONSIDERAR

    dl_tail_loss, colors, names = getCOV(data_tailloss_dl, extra_info, 'min_snr_used', dropna= False, preRunattr = preRunattr)

    fig = px.ecdf(dl_tail_loss, x="Mean", color=colors, labels= {"Mean": "Loss rate", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: TailLoss per UE DL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE TEMPO E PERDAS - VER COMO CONSIDERAR

    ul_tail_loss, colors, names = getCOV(data_tailloss_ul, extra_info, 'min_snr_used', preRunattr = preRunattr)

    fig = px.ecdf(ul_tail_loss, x="Mean", color=colors, labels= {"Mean": "Loss rate", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Tail Loss per UE UL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE TEMPO E PERDAS - VER COMO CONSIDERAR

    dl_play_loss, colors, names = getCOV(data_playloss_dl, extra_info, 'min_snr_used', preRunattr = preRunattr)

    fig = px.ecdf(dl_play_loss, x="Mean", color=colors, labels= {"Mean": "Loss rate", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: PlayoutLoss per UE DL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE TEMPO E PERDAS - VER COMO CONSIDERAR

    ul_play_loss, colors, names = getCOV(data_playloss_ul, extra_info, 'min_snr_used', preRunattr = preRunattr)

    fig = px.ecdf(ul_play_loss, x="Mean", color=colors, labels= {"Mean": "Loss rate", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: PlayoutLoss per UE UL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE TEMPO E PERDAS - VER COMO CONSIDERAR

    loss_dl = gen_ues_data_single(data_frameloss_dl, num_ues, directions) + gen_ues_data_single(data_playloss_dl, num_ues, directions) + gen_ues_data_single(data_tailloss_dl, num_ues, directions)

    mean_loss_dl, colors, names = getCOV(loss_dl, extra_info, 'min_snr_used', preRunattr = preRunattr)

    fig = px.ecdf(mean_loss_dl, x="Mean", color=colors, labels= {"Mean": "Loss rate", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Total Loss per UE DL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    loss_ul = gen_ues_data_single(data_frameloss_ul, num_ues, directions) + gen_ues_data_single(data_playloss_ul, num_ues, directions) + gen_ues_data_single(data_tailloss_ul, num_ues, directions)

    mean_loss_ul, colors, names = getCOV(loss_ul, extra_info, 'min_snr_used', preRunattr = preRunattr)

    fig = px.ecdf(mean_loss_ul, x="Mean", color=colors, labels= {"Mean": "Loss rate", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Total Loss per UE UL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    #TODO: usar sinr uplink?
    #mean_loss = getMultiCOV(loss, extra_info, repetitions, skipna= False)

    #mean_loss["sinr"] = mean_sinr["Mean"]

    #fig = px.scatter(mean_loss, x= "sinr",  y= "Mean", color="name", labels= {"Mean": "Loss rate", "sinr": "Sinr Downlink"}, #range_x = (-(10**-7), 10**-6),
    #                 title= "SLICED: Loss per UE", log_y = True)

    #fig.show()

    """**Jitter < 0.4s**"""

    mean_jitter, colors, names = getCOV(jitter, extra_info, 'min_snr_used', preRunattr = preRunattr)

    fig = px.ecdf(mean_jitter, x="Mean", color=colors, labels= {"Mean": "Jitter (s)", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  marginal="rug", title= "SLICED: Jitter per UE - CDF", hover_data = ["COV"], hover_name = names)

    #fig.show()

    dl_jitter, colors, names = getCOV(data_jitter_dl.fillna(0), extra_info, 'min_snr_used', preRunattr = preRunattr)

    fig = px.ecdf(dl_jitter, x="Mean", color=colors, labels= {"Mean": "Jitter (s)", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Jitter per UE DL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE TEMPO E PERDAS - VER COMO CONSIDERAR
    # No caso substituido por 0 pois não existe NaN no throughput, entao os NaN restantes são 0 .

    thr_tmp = gen_ues_data_single(dataUL, num_ues, directions)
    jul_tmp = gen_ues_data_single(data_jitter_ul, num_ues, directions)

    tmp_data_jitter_ul = thr_tmp.notna().replace(False, np.nan).replace(True, 1) * jul_tmp.fillna(0)

    ul_jitter, colors, names = getCOV(tmp_data_jitter_ul, extra_info, 'min_snr_used', dropna= False, preRunattr = preRunattr)

    fig = px.ecdf(ul_jitter, x="Mean", color=colors, labels= {"Mean": "Jitter (s)", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Jitter per UE UL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE TEMPO E PERDAS - VER COMO CONSIDERAR

    """**MOS:**"""

    dl_mos, colors, names = getCOV(data_mos_dl, extra_info, 'min_snr_used', preRunattr = preRunattr)

    fig = px.ecdf(dl_mos, x="Mean", color=colors, labels= {"Mean": "MOS", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: MOS per UE DL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DE MOS - CONSIDERAR COMO 1 (PIOR NOTA)?

    fig = px.ecdf(dl_mos, x="COV", color=colors, labels= {"Mean": "MOS", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: MOS COV per UE DL - CDF", hover_data = ["Mean"], hover_name = names)

    fig.show()

    ul_mos, colors, names = getCOV(data_mos_ul.fillna(1), extra_info, 'min_snr_used', preRunattr = preRunattr)

    fig = px.ecdf(ul_mos, x="Mean", color=colors, labels= {"Mean": "MOS", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: MOS per UE UL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DE MOS - CONSIDERAR COMO 1 (PIOR NOTA)?

    fig = px.ecdf(ul_mos, x="COV", color=colors, labels= {"Mean": "MOS", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: MOS COV per UE UL - CDF", hover_data = ["Mean"], hover_name = names)

    fig.show()

def comparing_video_ilptype(chosen_seeds: List[int], modes: List[str], project_dir: str, sim_dir: str, csv_dir: str, images_dir: str= "Images", extra_config_name: str= '',
                            extra_dir: List[str] = [], height: int= 500, width: int= 700, cov: bool= True, interference: bool= False,
                            lambda_poisson: int = 30, num_slices: int = 12, only_enb_data: bool = False, enb_data: str = "NumEnbs", **kwargs):
  """## **Comparing**"""

  modes = genf.verify_modes(modes)

  for param in extra_dir:
    sim_dir += '/' + (f'{param}_{kwargs[param]}' if param in kwargs else '')
    images_dir += '/' + (f'{param}_{kwargs[param]}' if param in kwargs else '')
    csv_dir += '/' + (f'{param}_{kwargs[param]}' if param in kwargs else '')
  Path(images_dir).mkdir(parents=True, exist_ok=True)

  extra = False

  #data_frames = {}
  csvs_info = {}
  ues_per_slice = {}
  for mode in modes:
    #data_frames[mode] = pd.DataFrame()
    csvs_info[mode] = []
    for chosen_seed in chosen_seeds:
      sim_dir_full = sim_dir + f'/chosen_seed_{chosen_seed}'
      csv_dir_full = csv_dir + f'/chosen_seed_{chosen_seed}'
      sim_path =  project_dir + '/' + sim_dir_full
      results_path = project_dir + '/' + csv_dir_full
      csv_path, _ = genf.gen_csv_path(mode= mode, sim_path= sim_path, results_path= results_path, extra_config_name= extra_config_name, interference=interference)
      #new_data_frame = pd.read_csv(csv_path)
      #new_data_frame['run'] = new_data_frame['run'].astype(str) + f'_seed_{chosen_seed}'
      #print(csv_path)
      #data_frames[mode] = pd.concat([data_frames[mode], new_data_frame])
      csvs_info[mode].append({"seed": chosen_seed, "path": csv_path})
      #print(f'New data frame index: {new_data_frame.index}')
      #print(f'Result data frame index: {data_frames[mode].index}')

      users_t_m = genf.gen_users_t_m(chosen_seed, lambda_poisson = lambda_poisson, num_slices=num_slices)     
      ues_per_slice[str(chosen_seed)] = genf.gen_ue_per_slice(chosen_seed, users_t_m, num_slices=num_slices)
      #with open('test.txt', 'w') as f:
      #  f.write(str(ues_per_slice[str(chosen_seed)]))

  """### Mode1 x Mode2 (power 30 dBm)"""
  all_throughput: pd.DataFrame
  all_sinr: pd.DataFrame
  all_enb: pd.DataFrame
  all_enb_hist: pd.DataFrame
  all_enddelay: pd.DataFrame
  all_rcvd_packets: pd.DataFrame
  all_packets_sent: pd.DataFrame
  
  if only_enb_data:
    all_enb, all_enb_hist = compare_csvs_video(csvs_info=csvs_info, dict_ids={'ILP' : [mode.capitalize() for mode in modes], 'Power': [30 for _ in modes]},
                                                                                                                            extra= extra, ues_per_slice= ues_per_slice, only_enb_data=only_enb_data, enb_data=enb_data)
  elif extra:
    all_throughput, all_sinr, all_enb, all_enb_hist, all_enddelay, all_rcvd_packets, all_packets_sent = compare_csvs_video(csvs_info=csvs_info, dict_ids={'ILP' : [mode.capitalize() for mode in modes], 'Power': [30 for _ in modes]},
                                                                                                                            extra= extra, ues_per_slice= ues_per_slice)
  else:
    all_throughput, all_sinr, all_enb, all_enb_hist = compare_csvs_video(csvs_info=csvs_info, dict_ids={'ILP' : [mode.capitalize() for mode in modes], 'Power': [30 for _ in modes]}, extra= extra, ues_per_slice= ues_per_slice)
    #print('Not extra: ', all_throughput['Mean'])  

  #print(all_throughput['Mean'].index.get_level_values('n_obj'))

  snr_order = ['5', '10', '15']                                                                                                       

  if only_enb_data:
    if enb_data == "NumEnbs":
      str_ytitle = "NumEnbs"#"Average Number of Vehicles"
    elif enb_data == "NumSliceMaxEnbs":
      str_ytitle = "NumSliceMaxEnbs"
    elif enb_data == "MeanNumSliceConstEnbs":
      str_ytitle = "MeanNumSliceConstEnbs"
    elif enb_data == "MeanNumSliceConstEnbs++1":
      str_ytitle = "MeanNumSliceConstEnbs++1"
    elif enb_data == "MaxAddEnbs":
      str_ytitle = "MaxAddEnbs"#"Maximum Added Vehicles to Cenario"    #TODO: melhorar o título
    elif enb_data == "NumAddNumEnbs":
      str_ytitle = "NumAddNumEnbs"
    elif enb_data == "MeanAddNumEnbs":
      str_ytitle = "MeanAddNumEnbs"
    elif enb_data == "NumAddNumEnbsw0":
      str_ytitle = "NumAddNumEnbsw0"
    elif enb_data == "MeanAddNumEnbsw0":
      str_ytitle = "MeanAddNumEnbsw0"
    
    print("Plotting eNB " + enb_data)
    x = all_enb.index.get_level_values("min_snr_used").tolist()

    names = all_enb.index.get_level_values('n_obj').tolist()

    colors = [genf.MODES_NEW_NAMES[m.lower()] for m in all_enb.index.get_level_values("ILP").tolist()]

    facet = all_enb.index.get_level_values("Power").tolist()
    
    fig = px.bar(all_enb, x= x, y= "Mean", color= colors, labels= {"x" : "Min SNR (dB)" , "Mean": str_ytitle, "facet_col": "Potência (dBm)", "color": "Algorithm"},
                #title= "Média do número de eNodeBs em cada simulação",
                hover_name = names, error_y = "ERR", barmode = 'group', category_orders={"color": genf.MODES_NEW_NAMES.values(), "x": snr_order}, 
                color_discrete_map={"AID": COLOR_AID,
                                    "TID": COLOR_TID, #
                                    "PGWO": COLOR_PGWO, #
                                    "PGD": COLOR_PGD}) #

    """
    if enb_data == "NumEnbs":
      x = all_enb_max.index.get_level_values("min_snr_used").tolist()
      names = all_enb_max.index.get_level_values('n_obj').tolist()
      colors = [genf.MODES_NEW_NAMES[m.lower()] for m in all_enb_max.index.get_level_values("ILP").tolist()]
      facet = all_enb_max.index.get_level_values("Power").tolist()

      fig2 = px.bar(all_enb_max, x= x, y= "Mean", color= colors, labels= {"x" : "Min SNR (dB)" , "Mean": str_ytitle, "facet_col": "Potência (dBm)", "color": "Algorithm"},
                #title= "Média do número de eNodeBs em cada simulação",
                hover_name = names, error_y = "ERR", barmode = 'group', category_orders={"color": genf.MODES_NEW_NAMES.values(), "x": snr_order}, 
                color_discrete_map={"AID":"grey",
                                    "TID":"grey",
                                    "PGWO":"grey",
                                    "PGD":"grey"})

      fig2.update_layout(font=dict(size=11))
      fig2.update_yaxes(type="log")
      fig2.update_yaxes(range=[0, np.log10(35)])
      fig2.write_image(images_dir+"/"+"enb_ilptype_test"+enb_data+".svg", height= height, width= width)

      fig.add_bar(all_enb_max, x= x, y= "Mean", color= colors, labels= {"x" : "Min SNR (dB)" , "Mean": str_ytitle, "facet_col": "Potência (dBm)", "color": "Algorithm"},
                #title= "Média do número de eNodeBs em cada simulação",
                hover_name = names, error_y = "ERR", barmode = 'group', category_orders={"color": genf.MODES_NEW_NAMES.values(), "x": snr_order}, 
                color_discrete_map={"AID":"grey",
                                    "TID":"grey",
                                    "PGWO":"grey",
                                    "PGD":"grey"})
    """
    fig.update_layout(font=dict(size=13))
    fig.show()
    islog = False
    if islog:
      fig.update_yaxes(type="log")
      if (enb_data == "NumSliceMaxEnbs" or enb_data == "MeanNumSliceConstEnbs++1" or enb_data == "MeanNumSliceConstEnbs"):
        fig.update_yaxes(range=[0, np.log10(15)])
      elif (enb_data == "MeanAddNumEnbs" or enb_data == "MeanAddNumEnbsw0" or enb_data == "NumAddNumEnbsw0"):
        fig.update_yaxes(range=[0, np.log10(10)])
      elif enb_data == "NumAddNumEnbs":
        fig.update_yaxes(range=[0, np.log10(6)])
      elif enb_data == "MaxAddEnbs":
        fig.update_yaxes(range=[0, np.log10(25)])
      elif enb_data == "NumEnbs":
        fig.update_yaxes(range=[0, np.log10(35)])
    else:
      if (enb_data == "NumSliceMaxEnbs" or enb_data == "MeanNumSliceConstEnbs++1" or enb_data == "MeanNumSliceConstEnbs"):
        fig.update_yaxes(range=[0, 15])
      elif (enb_data == "MeanAddNumEnbs" or enb_data == "MeanAddNumEnbsw0" or enb_data == "NumAddNumEnbsw0"):
        fig.update_yaxes(range=[0, 10])
      elif enb_data == "NumAddNumEnbs":
        fig.update_yaxes(range=[0, 6])
      elif enb_data == "MaxAddEnbs":
        fig.update_yaxes(range=[0, 25])
      elif enb_data == "NumEnbs":
        fig.update_yaxes(range=[0, 35])

    fig.write_image(images_dir+"/"+"enb_ilptype_"+enb_data+".svg", height= height, width= width)

    all_enb_hist.to_excel(images_dir+"/"+'enb_data.xlsx', sheet_name= 'ILPCompare')

    tmp = np.unique(all_enb_hist.index.get_level_values("min_snr_used").tolist())

    for n in tmp:
      tmp_enb_hist = all_enb_hist.xs(n, level='min_snr_used')

      shape = [genf.MODES_NEW_NAMES[m.lower()] for m in tmp_enb_hist.index.get_level_values("ILP").tolist()]

      facet = tmp_enb_hist.index.get_level_values("Power").tolist()

      fig = px.histogram(tmp_enb_hist, x= 'NumEnbs', height= height, width= width, labels= {"x" : "Number eNBs" ,"pattern_shape" : "Min Snr Used (dB)", "Mean": "Mean of Used Enbs", "facet_col": "Power", "color": "Solver Type"},
                        title= f"NumEnbs in each Simulation - {n} Min SNR", pattern_shape= shape, barmode = 'group', category_orders={"color": genf.MODES_NEW_NAMES.values(), "line_dash": snr_order})

      fig.write_image(images_dir+"/"+f"enb_ilptype_{n}hist.svg", height= height, width= width)
    return

  print('Plotting throughput.')

  lines = all_throughput.index.get_level_values("min_snr_used").tolist()

  names = all_throughput.index.get_level_values('n_obj').tolist()

  colors = [genf.MODES_NEW_NAMES[m.lower()] for m in all_throughput.index.get_level_values("ILP").tolist()]

  facet = all_throughput.index.get_level_values("Power").tolist()

  fig = px.ecdf(all_throughput, x='Mean', color = colors, labels= {"Mean": "Average Throughput - Downlink (bps)", "line_dash": "Min SNR (dB)", "color": "Algorithm", "facet_col": "Potência(dBm)", "y": "Probabilidade"}, markers= False, lines= True,
                #title= "CDF do throughput recebido por cada UE",
                ecdfmode="reversed", hover_name = names, line_dash= lines, category_orders={"color": genf.MODES_NEW_NAMES.values(), "line_dash": snr_order},
                range_x=(0,9*10**6), color_discrete_map={"AID": COLOR_AID,
                                                          "TID": COLOR_TID, #
                                                          "PGWO": COLOR_PGWO, #
                                                          "PGD": COLOR_PGD})
  fig.update_layout(dict1={})
  fig.update_layout(font=dict(size=11))
  fig.update_layout(yaxis_title='Cumulative Probability')

  fig.write_image(images_dir+"/"+"thr_ilptype.svg", height= height, width= width)

  if cov:
    fig = px.ecdf(all_throughput, x='COV', color = colors, labels= {"COV": "Throughput:Médio COV", "line_dash": "Min SNR (dB)", "color": "Otimizador", "facet_col": "Potência(dBm)", "y": "Probabilidade"}, markers= False, lines= True,
                  title= "UEs Throughput COV DL - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": genf.MODES_NEW_NAMES.values(), "line_dash": snr_order})

    fig.write_image(images_dir+"/"+"thr_ilptype_cov.svg", height= height, width= width)

  #median_data = tmp_thr.groupby(["min_snr_used", "ILP", "RBs"], dropna = False).median()
  print('Plotting eNBs.')
  x = all_enb.index.get_level_values("min_snr_used").tolist()

  names = all_enb.index.get_level_values('n_obj').tolist()

  colors = [genf.MODES_NEW_NAMES[m.lower()] for m in all_enb.index.get_level_values("ILP").tolist()]

  shape = [genf.MODES_NEW_NAMES[m.lower()] for m in all_enb.index.get_level_values("ILP").tolist()]

  facet = all_enb.index.get_level_values("Power").tolist()

  fig = px.bar(all_enb, x= x, y= "Mean", color= colors, labels= {"x" : "Minimum QoS - SNR (dB)" , "Mean": "Average Number of Vehicles", "facet_col": "Potência (dBm)", "color": "Algorithm", "pattern_shape": "Algorithm"},
              #title= "Média do número de eNodeBs em cada simulação",
              hover_name = names, error_y = "ERR", barmode = 'group', category_orders={"color": genf.MODES_NEW_NAMES.values(), "x": snr_order},
              color_discrete_map={"AID": COLOR_AID,
                                  "TID": COLOR_TID, #
                                  "PGWO": COLOR_PGWO, #
                                  "PGD": COLOR_PGD}, pattern_shape=shape)

  # Atualize os rótulos da legenda para exibir apenas a categoria (AID, TID, PGWO, PGD)
  fig.update_traces(showlegend=True)
  fig.update_layout(legend_title_text='Algorithm')                                  

  fig.update_layout(font=dict(size=13))
  fig.update_yaxes(range=[0, 35])

  fig.write_image(images_dir+"/"+"enb_ilptype.svg", height= height, width= width)

  all_enb_hist.to_excel(images_dir+"/"+'enb_data.xlsx', sheet_name= 'ILPCompare')

  tmp = np.unique(all_enb_hist.index.get_level_values("min_snr_used").tolist())

  for n in tmp:
    tmp_enb_hist = all_enb_hist.xs(n, level='min_snr_used')

    shape = [genf.MODES_NEW_NAMES[m.lower()] for m in tmp_enb_hist.index.get_level_values("ILP").tolist()]

    facet = tmp_enb_hist.index.get_level_values("Power").tolist()

    fig = px.histogram(tmp_enb_hist, x= 'NumEnbs', height= height, width= width, labels= {"x" : "Number eNBs" ,"pattern_shape" : "Min Snr Used (dB)", "Mean": "Mean of Used Enbs", "facet_col": "Power", "color": "Solver Type"},
                       title= f"NumEnbs in each Simulation - {n} Min SNR", pattern_shape= shape, barmode = 'group', category_orders={"color": genf.MODES_NEW_NAMES.values(), "line_dash": snr_order})

    fig.write_image(images_dir+"/"+f"enb_ilptype_{n}hist.svg", height= height, width= width)
  return  #TODO: REMOVE
  sp = np.sqrt(((30-1)*0.9660918**2 + (30-1)*0.8164966**2)/(30+30-2))
  t = (3.4 - 3)/(sp * np.sqrt(2/30))
  #print(t)
  print('Plotting SINR.')
  lines = all_sinr.index.get_level_values("min_snr_used").tolist()

  names = all_sinr.index.get_level_values('n_obj').tolist()

  colors = [genf.MODES_NEW_NAMES[m.lower()] for m in all_sinr.index.get_level_values("ILP").tolist()]

  facet = all_sinr.index.get_level_values("Power").tolist()

  fig = px.ecdf(all_sinr, x='Mean', color = colors, labels= {"Mean": "Average SNR - Downlink (dB)", "line_dash": "Min SNR (dB)", "color": "Algorithm", "facet_col": "Potência(dBm)", "y": "Probabilidade"}, markers= False, lines= True,
                #title= "CDF do SNR médio recebido por cada UE",
                ecdfmode="reversed", hover_name = names, line_dash= lines, 
                category_orders={"color": genf.MODES_NEW_NAMES.values(), "line_dash": snr_order},
                range_x=(-10, 35), color_discrete_map={"AID": COLOR_AID,
                                                        "TID": COLOR_TID, #
                                                        "PGWO": COLOR_PGWO, #
                                                        "PGD": COLOR_PGD})

  fig.update_layout(font=dict(size=11))
  fig.update_layout(yaxis_title='Cumulative Probability')

  default_lines = ['solid', 'dot','dash', 'longdash', 'dashdot', 'longdashdot']
  for i in range(len(snr_order)):
    fig.add_vline(x=int(snr_order[i]), line_width=1, line_dash=default_lines[i], line_color="gray", name=snr_order[i])
  
  fig.write_image(images_dir+"/"+"sinr_ilptype.svg", height= 500, width= width)

  if cov:
    fig = px.ecdf(all_sinr, x='COV', color = colors, labels= {"COV": "SNR:Médio COV", "color": "Min SNR (dB)", "line_dash": "Otimizador", "facet_col": "Potência(dBm)", "y": "Probabilidade"}, markers= False, lines= True,
                  title= "UE Sinr DL COV - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": genf.MODES_NEW_NAMES.values(), "line_dash": snr_order})

    fig.write_image(images_dir+"/"+"sinr_ilptype_cov.svg", height= height, width= width)

  if extra:

    lines = all_enddelay.index.get_level_values("min_snr_used").tolist()

    names = all_enddelay.index.get_level_values('n_obj').tolist()

    colors = all_enddelay.index.get_level_values("ILP").tolist()

    facet = all_enddelay.index.get_level_values("Power").tolist()

    fig = px.ecdf(all_enddelay, x='Mean', color = colors, labels= {"Mean": "Delay (s)", "line_dash": "Min Snr Used (dB)", "color": "ILP Type", "facet_col": "Power"}, markers= False, lines= True,
                  title= "End to End Delay of each UE DL - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

    fig.write_image(images_dir+"/"+"edd_ilptype.svg", height= height, width= width)

    if cov:
      fig = px.ecdf(all_enddelay, x='COV', color = colors, labels= {"COV": "COV", "line_dash": "Min Snr Used (dB)", "color": "ILP Type", "facet_col": "Power"}, markers= False, lines= True,
                    title= "End to End Delay COV of each UE DL - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

      fig.write_image(images_dir+"/"+"edd_ilptype_cov.svg", height= height, width= width)

    lines = all_rcvd_packets.index.get_level_values("min_snr_used").tolist()

    names = all_rcvd_packets.index.get_level_values('n_obj').tolist()

    colors = all_rcvd_packets.index.get_level_values("ILP").tolist()

    facet = all_rcvd_packets.index.get_level_values("Power").tolist()

    fig = px.ecdf(all_rcvd_packets, x='Mean', color = colors, labels= {"Mean": "Number of Received Packets", "line_dash": "Min Snr Used (dB)", "color": "ILP Type", "facet_col": "Power"}, markers= False, lines= True,
                  title= "Received packets by each UE DL - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

    fig.write_image(images_dir+"/"+"rcvdpkt_ilptype.svg", height= height, width= width)

    lines = all_packets_sent.index.get_level_values("min_snr_used").tolist()

    names = all_packets_sent.index.get_level_values('n_obj').tolist()

    colors = all_packets_sent.index.get_level_values("ILP").tolist()

    facet = all_packets_sent.index.get_level_values("Power").tolist()

    fig = px.ecdf(all_packets_sent, x='Mean', color = colors, labels= {"Mean": "Number of Packets Sent", "line_dash": "Min Snr Used (dB)", "color": "ILP Type", "facet_col": "Power"}, markers= False, lines= True,
                  title= "Packets sent to each UE DL - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

    fig.write_image(images_dir+"/"+"pktsent_ilptype.svg", height= height, width= width)

  return

def comparing_video_powers(chosen_seeds: List[int], modes: Union[List[str], str], micro_powers: List[int], project_dir: str, sim_dir: str, csv_dir: str,
                           images_dir: str= "Images", extra_config_name: str= '', extra_dir: List[str] = [], height: int= 500, width: int= 700,
                           cov: bool= True, **kwargs):

  #Accepting list or a single mode str
  if type(modes) is list:
    modes = genf.verify_modes(modes)
  else:
    check_mode(modes)
    modes = [modes]

  #Comparing for each mode
  for mode in modes:
    comparing_video_powers_singlemode(chosen_seeds= chosen_seeds, mode= mode, micro_powers= micro_powers, project_dir= project_dir, sim_dir = sim_dir, csv_dir= csv_dir, images_dir= images_dir,
                                      extra_config_name= extra_config_name, extra_dir = extra_dir, height= height, width= width, cov= cov, **kwargs)

def comparing_video_powers_singlemode(chosen_seeds: List[int], mode: str, micro_powers: List[int], project_dir: str, sim_dir: str, csv_dir: str, images_dir: str= "Images",
                                      extra_config_name: str= '', extra_dir: List[str] = [], height: int= 500, width: int= 700, cov: bool= True, **kwargs):
  """### Comparing Powers"""

  check_mode(mode)

  name = 'x'.join([str(micro_power) for micro_power in micro_powers])

  extra_dir = extra_dir
  for param in extra_dir:
    sim_dir += '/' + (f'{param}_{kwargs[param]}' if param in kwargs else '')
    images_dir += '/' + (f'{param}_{kwargs[param]}' if param in kwargs else '')
    csv_dir += '/' + (f'{param}_{kwargs[param]}' if param in kwargs else '')
  Path(images_dir).mkdir(parents=True, exist_ok=True)

  data_frames = {}
  for micro_power in micro_powers:
    data_frames[micro_power] = pd.DataFrame()

    for chosen_seed in chosen_seeds:
      sim_dir_full = sim_dir + f'/micro_power_{micro_power}/chosen_seed_{chosen_seed}'
      csv_dir_full = csv_dir + f'/micro_power_{micro_power}/chosen_seed_{chosen_seed}'
      sim_path =  project_dir + '/' + sim_dir_full
      results_path = project_dir + '/' + csv_dir_full
      csv_path, _ = genf.gen_csv_path(mode= mode, sim_path= sim_path, results_path= results_path, extra_config_name= extra_config_name)
      new_data_frame = pd.read_csv(csv_path)
      print(csv_path)
      data_frames[micro_power] = pd.concat([data_frames[micro_power], new_data_frame])

  all_throughput, all_sinr, all_enb, all_enb_hist = compare_csvs_video([data_frames[micro_power] for micro_power in micro_powers],
                                                                       {'ILP' : [mode.capitalize() for _ in micro_powers], 'Power': [micro_power for micro_power in micro_powers]},
                                                                       extra= False)
  colors = all_throughput.index.get_level_values("min_snr_used").tolist()

  names = all_throughput.index.get_level_values('n_obj').tolist()

  lines = all_throughput.index.get_level_values("Power").tolist()

  facet = all_throughput.index.get_level_values("ILP").tolist()

  fig = px.ecdf(all_throughput, x='Mean', color = colors, labels= {"Mean": "Throughput:Mean (Bps)", "color": "Min Snr Used (dB)", "line_dash": "Transmission Power (dBm)", "facet_col": "ILP Type"}, markers= False, lines= True,
                title= f"UE Throughput {mode.capitalize()} DL - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

  fig.write_image(images_dir+f"/thr_{name}_{mode}.svg", height= height, width= width)

  if cov:
    fig = px.ecdf(all_throughput, x='COV', color = colors, labels= {"COV": "Throughput:Mean COV", "color": "Min Snr Used (dB)", "line_dash": "Transmission Power (dBm)", "facet_col": "ILP Type"}, markers= False, lines= True,
                  title= f"UE Throughput {mode.capitalize()} DL COV - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

    fig.write_image(images_dir+f"/thr_{name}_{mode}_cov.svg", height= height, width= width)

  colors = all_enb.index.get_level_values("min_snr_used").tolist()

  names = all_enb.index.get_level_values('n_obj').tolist()

  shape = all_enb.index.get_level_values("Power").tolist()

  facet = all_enb.index.get_level_values("ILP").tolist()

  #median_data = tmp_thr.groupby(["min_snr_used", "ILP", "RBs"], dropna = False).median()

  fig = px.bar(all_enb, x= colors, y= "Mean", color= colors, labels= {"x" : "Min Snr Used (dB)" ,"color" : "Transmission Power (dBm)", "Mean": "Mean of Used Enbs", "facet_col": "ILP Type", "pattern_shape": "Transmission Power (dBm)"},
              title= f"Mean Num Enbs per Simulation {mode.capitalize()}", hover_name = names, error_y = "Std", pattern_shape= shape, barmode = 'group', facet_col= facet, category_orders={"color": ["5", "10", "15"]})
  fig.write_image(images_dir+f"/enb_{name}_{mode}.svg", height= height, width= width)

  """#### Extra"""

  colors = all_sinr.index.get_level_values("min_snr_used").tolist()

  names = all_sinr.index.get_level_values('n_obj').tolist()

  lines = all_sinr.index.get_level_values("Power").tolist()

  facet = all_sinr.index.get_level_values("ILP").tolist()

  fig = px.ecdf(all_sinr, x='Mean', color = colors, labels= {"Mean": "Sinr:Mean (dB)", "color": "Min Snr Used (dB)", "line_dash": "Transmission Power (dBm)", "facet_col": "ILP Type"}, markers= False, lines= True,
                title= f"UE Sinr {mode.capitalize()} DL - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

  fig.write_image(images_dir+f"/sinr_{name}_{mode}.svg", height= height, width= width)

  if cov:
    fig = px.ecdf(all_sinr, x='COV', color = colors, labels= {"COV": "Sinr:Mean COV", "color": "Min Snr Used (dB)", "line_dash": "Transmission Power (dBm)", "facet_col": "ILP Type"}, markers= False, lines= True,
                  title= f"UE Sinr DL {mode.capitalize()} COV - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

    fig.write_image(images_dir+f"/sinr_{name}_{mode}_cov.svg", height= height, width= width)

  return

  """### Disasters"""

"""**COV (Coeficiente de Variação)**

For menor ou igual a 15% → baixa dispersão: dados homogêneos

For entre 15 e 30% → média dispersão

For maior que 30% → alta dispersão: dados heterogêneos
"""

def comparing_voip():

  initialDataPS = pd.read_csv('/content/drive/MyDrive/Pesquisa_Giordano_Juliano/SimuLTE/dados/ILP/ilp_fixed_sliced_100ps.csv')
  initialData = pd.read_csv('/content/drive/MyDrive/Pesquisa_Giordano_Juliano/SimuLTE/dados/ILP/ilp_fixed_sliced.csv')
  num_ues = 60
  directions = 2

  preItervarPS, preRunattrPS, preVectorPS, preScalarPS, extra_info_ps, num_enbs_ps = processInitialData(initialDataPS)
  preItervar, preRunattr, preVector, preScalar, extra_info, num_enbs = processInitialData(initialData)

  dataDLPS = get_data_from_scalar("voIPReceivedThroughput:mean", "ue", preScalarPS, num_ues, 1)
  dataDL = get_data_from_scalar("voIPReceivedThroughput:mean", "ue", preScalar, num_ues, 1)

  dl_thr_PS, colorsPS, namesPS = getCOV(dataDLPS, extra_info_ps, 'min_snr_used', True, unite= True, preRunattr = preRunattrPS)

  dl_thr, colors, names = getCOV(dataDL, extra_info, 'min_snr_used', True, unite= True, preRunattr = preRunattr)

  tmp_thr = pd.concat([dl_thr, dl_thr_PS], keys= [40, 100], names = ["PS"])

  colors = tmp_thr.index.get_level_values("min_snr_used").tolist()

  names = tmp_thr.index.get_level_values('n_obj').tolist()

  symbols = tmp_thr.index.get_level_values("PS").tolist()

  fig = px.ecdf(tmp_thr, x='Mean', color = colors, labels= {"Mean": "Throughput:Mean (Bps)", "color": "Min Snr Used (dB)", "line_dash": "Package Size"}, markers= False, lines= True,
                title= "HANDO: Throughput DL per UE - CDF", ecdfmode="reversed", hover_name = names, line_dash= symbols)

  fig.show()

def comparing_interference(chosen_seeds: List[int], mode: str, project_dir: str, sim_dir: str, csv_dir: str, images_dir: str= "Images", extra_config_name: str= '',
                           extra_dir: List[str] = [], height: int= 500, width: int= 700, cov: bool= True, **kwargs):
  
  check_mode(mode)

  for param in extra_dir:
    sim_dir += '/' + (f'{param}_{kwargs[param]}' if param in kwargs else '')
    images_dir += '/' + (f'{param}_{kwargs[param]}' if param in kwargs else '')
    csv_dir += '/' + (f'{param}_{kwargs[param]}' if param in kwargs else '')
  Path(images_dir).mkdir(parents=True, exist_ok=True)

  data_frames = {}
  for inter in [False, True]:
    data_frames[inter] = pd.DataFrame()
    for chosen_seed in chosen_seeds:
      sim_dir_full = sim_dir + f'/chosen_seed_{chosen_seed}'
      csv_dir_full = csv_dir + f'/chosen_seed_{chosen_seed}'
      sim_path =  project_dir + '/' + sim_dir_full
      results_path = project_dir + '/' + csv_dir_full
      csv_path, _ = genf.gen_csv_path(mode= mode, sim_path= sim_path, results_path= results_path, extra_config_name= extra_config_name, interference=inter)
      new_data_frame = pd.read_csv(csv_path)
      print(csv_path)
      data_frames[inter] = pd.concat([data_frames[inter], new_data_frame])

  all_throughput, all_sinr, all_enb, all_enb_hist, all_enddelay, all_rcvd_packets, all_packets_sent = compare_csvs_video([data_frames[inter] for inter in [False, True]], {'ILP' : [mode.capitalize() for _ in [False, True]], 'Power': [30 for _ in [False, True]]},
                                                                                                                          extra= True)

  # Throughput

  colors = all_throughput.index.get_level_values("min_snr_used").tolist()

  names = all_throughput.index.get_level_values('n_obj').tolist()

  lines = all_throughput.index.get_level_values("Inter").tolist()

  facet = all_throughput.index.get_level_values("Power").tolist()

  fig = px.ecdf(all_throughput, x='Mean', color = colors, labels= {"Mean": "Throughput:Mean (Bps)", "color": "Min Snr Used (dB)", "line_dash": "Interference", "facet_col": "Power"}, markers= False, lines= True,
                title= f"UEs Throughput DL - {mode} - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})
  
  fig.write_image(images_dir+"/"+f"thr_inter_{mode}.svg", height= height, width= width)

  if cov:
    fig = px.ecdf(all_throughput, x='COV', color = colors, labels= {"COV": "Throughput:Mean COV", "color": "Min Snr Used (dB)", "line_dash": "Interference", "facet_col": "Power"}, markers= False, lines= True,
                  title= f"UEs Throughput COV DL - {mode} - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

    fig.write_image(images_dir+"/"+f"thr_inter_cov_{mode}.svg", height= height, width= width)

  #End to End Delay

  colors = all_enddelay.index.get_level_values("min_snr_used").tolist()

  names = all_enddelay.index.get_level_values('n_obj').tolist()

  lines = all_enddelay.index.get_level_values("Inter").tolist()

  facet = all_enddelay.index.get_level_values("Power").tolist()

  fig = px.ecdf(all_enddelay, x='Mean', color = colors, labels= {"Mean": "Delay (s)", "color": "Min Snr Used (dB)", "line_dash": "Interference", "facet_col": "Power"}, markers= False, lines= True,
                title= f"End to End Delay of each UE DL - {mode} - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

  fig.write_image(images_dir+"/"+f"edd_inter_{mode}.svg", height= height, width= width)

  if cov:
    fig = px.ecdf(all_enddelay, x='COV', color = colors, labels= {"COV": "COV", "color": "Min Snr Used (dB)", "line_dash": "Interference", "facet_col": "Power"}, markers= False, lines= True,
                  title= f"End to End Delay COV of each UE DL - {mode} - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

    fig.write_image(images_dir+"/"+f"edd_inter_cov_{mode}.svg", height= height, width= width)

  # Received Packets

  colors = all_rcvd_packets.index.get_level_values("min_snr_used").tolist()

  names = all_rcvd_packets.index.get_level_values('n_obj').tolist()

  lines = all_rcvd_packets.index.get_level_values("Inter").tolist()

  facet = all_rcvd_packets.index.get_level_values("Power").tolist()

  fig = px.ecdf(all_rcvd_packets, x='Mean', color = colors, labels= {"Mean": "Number of Received Packets", "color": "Min Snr Used (dB)", "line_dash": "Interference", "facet_col": "Power"}, markers= False, lines= True,
                title= f"Received packets by each UE DL - {mode} - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

  fig.write_image(images_dir+"/"+f"rcvdpkt_inter_{mode}.svg", height= height, width= width)

  # Packets sent

  colors = all_packets_sent.index.get_level_values("min_snr_used").tolist()

  names = all_packets_sent.index.get_level_values('n_obj').tolist()

  lines = all_packets_sent.index.get_level_values("Inter").tolist()

  facet = all_packets_sent.index.get_level_values("Power").tolist()

  fig = px.ecdf(all_packets_sent, x='Mean', color = colors, labels= {"Mean": "Number of Packets Sent", "color": "Min Snr Used (dB)", "line_dash": "Interference", "facet_col": "Power"}, markers= False, lines= True,
                title= f"Packets sent to each UE DL - {mode} - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

  fig.write_image(images_dir+"/"+f"pktsent_inter_{mode}.svg", height= height, width= width)

  return

def hist_ues_slice():

  chosen_seeds = [2,3,4,5,6,7,10,11,12,13]
  num_slices = 12
  lambda_poisson_gen_users_t_m = 30

  df_hist = pd.DataFrame

  for chosen_seed in chosen_seeds:
    users_t_m = genf.gen_users_t_m(chosen_seed, lambda_poisson = lambda_poisson_gen_users_t_m, num_slices=num_slices) 
    ues_per_slice = genf.gen_ue_per_slice(chosen_seed, users_t_m, num_slices=num_slices)

  #fig = px.histogram(tmp_enb_hist, x= 'NumEnbs', height= height, width= width, labels= {"x" : "Number eNBs" ,"color" : "Min Snr Used (dB)", "Mean": "Mean of Used Enbs", "facet_col": "Power", "pattern_shape": "ILP Type"},
  #                    title= f"NumEnbs in each Simulation - {n} Min SNR", pattern_shape= shape, barmode = 'group', facet_col= facet, category_orders={"color": ["5", "10", "15"]})

  #fig.write_image(images_dir+"/"+f"enb_ilptype_{n}hist.svg", height= height, width= width)


if __name__ == "__main__":
  os.chdir("/home/juliano/Documentos/LTE-Scenarios-Simulation/Functions")
  chosen_seeds = [2,6]#[2,6,10,12,13,14,15,21,22,24,25]

  modes = ['single','fixed','pgwo2','ga']#['ga', 'single', 'fixed', 'pgwo2', 'pgwo3']#['single', 'fixed', 'ga'] 
  #num_ues= 60
  extra_dir = ['disaster_percentage','micro_power']
  disaster_percentage = 0 #Porcentagem do alastramento do desastre (%)
  micro_power = 30 #dBm
  sim_dir = '_5G/simulations'
  project_dir = '../Network_CCOpMv'
  csv_dir = '_5G/results'
  images_dir = "Images"
  extra_config_name= "video"
  height= 344#500
  width= 800#1200
  only_enb_data = True
  enb_data = ["NumAddNumEnbsw0"] # 0 NumEnbs,
                                 # 1 MaxAddEnbs
                                 # 2 MeanNumSliceConstEnbs
                                 # 3 MeanNumSliceConstEnbs++1
                                 # 4 NumAddNumEnbs
                                 # 5 MeanAddNumEnbs
                                 # 6 NumSliceMaxEnbs
                                 # 7 NumAddNumEnbsw0
                                 # 8 MeanAddNumEnbsw0
  cov = True #Cria as imagens do COV ou não
  interference = False
  num_slices = 12
  lambda_poisson_gen_users_t_m = 30

  kwargs = {'disaster_percentage': disaster_percentage, 'micro_power': micro_power}

  init = time.time()

  if not only_enb_data:
    comparing_video_ilptype(chosen_seeds= chosen_seeds, modes= modes, project_dir= project_dir, sim_dir = sim_dir, csv_dir= csv_dir, images_dir= images_dir,
                          extra_dir= extra_dir, extra_config_name= extra_config_name, height= height, width= width, cov= cov, interference= interference,
                          lambda_poisson=lambda_poisson_gen_users_t_m, num_slices=num_slices, only_enb_data=only_enb_data, enb_data=enb_data,
                          **kwargs)#Disaster and micropower as **kwargs
  else:
    for data in enb_data:
      comparing_video_ilptype(chosen_seeds= chosen_seeds, modes= modes, project_dir= project_dir, sim_dir = sim_dir, csv_dir= csv_dir, images_dir= images_dir,
                          extra_dir= extra_dir, extra_config_name= extra_config_name, height= height, width= width, cov= cov, interference= interference,
                          lambda_poisson=lambda_poisson_gen_users_t_m, num_slices=num_slices, only_enb_data=only_enb_data, enb_data=data,
                          **kwargs)#Disaster and micropower as **kwargs

  print(f'Total time: {(time.time() - init)/(60*60)} hours.')
  #comparing_interference(chosen_seeds=chosen_seeds, mode='fixed', project_dir=project_dir, sim_dir=sim_dir, csv_dir=csv_dir, images_dir=images_dir,
  #                       extra_config_name=extra_config_name, extra_dir=extra_dir, height=height, width=width, cov=cov,
  #                       **kwargs)

  #comparing_video_powers(chosen_seeds= chosen_seeds, modes= modes, micro_powers= [30], project_dir= project_dir, sim_dir = sim_dir, csv_dir= csv_dir, images_dir= images_dir,
  #                      extra_config_name= extra_config_name, extra_dir = ['disaster_percentage'], height= height, width= width, cov= cov,
  #                       **{'disaster_percentage': disaster_percentage})#Disaster as **kwarg

  #users_t_m = genf.gen_users_t_m(chosen_seed, lambda_poisson = lambda_poisson_gen_users_t_m, num_slices=num_slices)     
  #ues_per_slice = genf.gen_ue_per_slice(chosen_seed, users_t_m, num_slices=num_slices)

  print('Done.')
  
