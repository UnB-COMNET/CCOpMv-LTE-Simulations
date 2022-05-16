# -*- coding: utf-8 -*-
"""

Importar as bibliotecas do Pandas, Numpy, Sklearn

"""

import pandas as pd
import numpy as np
import plotly.express as px
import re

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

    scavetool x -o ilp_varying_sliced_video.csv -f "module(**.cellularNic.channelModel[*]) OR module(**.app[*])" ilp_varying_sliced_*_VIDEO/*-*.sca ilp_varying_sliced_*_VIDEO/*-*.vec
"""

def get_data_from_scalar (data_name: str, module: str, scalar_data, num_ues: int, num_macros: int):

  raw_module = scalar_data.apply(lambda x: x["module"][x["module"].find('.')+1:], axis=1)

  qname = raw_module + '.' + scalar_data.name

  pre_data = scalar_data.assign(qname = qname)

  data = pre_data[raw_module.str.match(module)]
  data = data[data["name"].str.startswith(data_name)]
  data = data.pivot('run', columns='qname', values='value')
  #count = num_ues*num_macros - data.isnull().sum(axis=1)

  return data

def get_data_from_vector (data_name: str, module: str, vector_data, num_ues: int, num_macros: int):

  raw_module = vector_data.apply(lambda x: x["module"][x["module"].find('.')+1:], axis=1)

  qname = raw_module + '.' + vector_data.name

  pre_data = vector_data.assign(qname = qname)

  data = pre_data[raw_module.str.match(module)]
  data = data[data["name"].str.startswith(data_name)]
  data = data.pivot('run', columns='qname', values=['vecvalue', 'vectime'])
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

def unite_slices (processed_data, id_info, repetition, dropna = True, slice_op= 'mean'):

  data = pd.concat([processed_data, id_info], axis= 1).assign(repetition = repetition)
  mean_data = pd.DataFrame()

  if slice_op == 'mean':
    mean_data = data.groupby(id_info.columns.tolist() + ["repetition"], dropna = dropna).mean()
  elif slice_op == 'sum':
    mean_data = data.groupby(id_info.columns.tolist() + ["repetition"], dropna = dropna).sum()
  elif slice_op == 'std':
    mean_data = data.groupby(id_info.columns.tolist() + ["repetition"], dropna = dropna).std()

  return mean_data

def compute_cov (data, columns, dropna: bool = True):

  mean_data = data.groupby(columns, dropna= dropna).mean()

  std_data = data.groupby(columns, dropna= dropna).std()

  cov_data = std_data/mean_data

  mean_data.columns = pd.MultiIndex.from_product([['Mean'], mean_data.columns])

  std_data.columns = pd.MultiIndex.from_product([['Std'], std_data.columns])

  cov_data.columns = pd.MultiIndex.from_product([['COV'], cov_data.columns])

  new_data = pd.concat([mean_data, std_data, cov_data], axis= 1).stack()

  new_data.index.names = new_data.index.names[:-1] + ['n_obj']

  return new_data
  #return new_data.reset_index(new_data.index.nlevels-1)

def getCOV(data, extra_info, color_column, repetition, dropna: bool = True, sliced: bool = True, slice_op= 'mean'):

  if sliced:
    tmp = unite_slices(data, extra_info, repetition, dropna, slice_op)
  else:
    tmp = pd.concat([data, extra_info], axis= 1)

  new_data = compute_cov(tmp, extra_info.columns.tolist(), dropna)

  colors = new_data.index.get_level_values(color_column).tolist()

  names = new_data.index.get_level_values('n_obj').tolist()

  return new_data, colors, names

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
  preItervar = itervar.pivot('run', columns='attrname', values='attrvalue').astype({"sched": object})
  preItervar = preItervar.drop(["sched", "Slice"], axis= 1)
  num_enbs = pd.DataFrame()
  num_enbs["NumEnbs"] = preItervar["NumEnbs"].astype({"NumEnbs": float})
  preItervar = preItervar.drop(["NumEnbs"], axis= 1)

  """Runattr processing"""
  preRunattr = runattr.pivot('run', columns='attrname', values='attrvalue').astype({"repetition": int})

  """Vector data pre-processing"""
  preVector = vector[vector.module != "_runattrs_"]

  """Scalar data pre-processing"""
  preScalar = scalar[scalar.module != "_runattrs_"]
  #.sctp with duplicated entries (?) than removed
  preScalar = preScalar[~preScalar["module"].str.endswith("sctp")]
  preData = preScalar.assign(qname = preScalar.module + '.' + preScalar.name)
  newData = preData.pivot('run', columns='qname', values='value')

  extra_info = preItervar.assign(min_snr_used = newData.index.str.findall(r'\d+').str[0])

  return preItervar, preRunattr, preVector, preScalar, extra_info, num_enbs

def get_data_vector_mean(data, operation= np.mean):
  data = data.applymap(lambda x: operation(list(map(float, x.split()))), na_action= 'ignore')
  return data

def compare_csvs_video(csvs, dict_ids: dict, num_ues, extra= False):

  results_throughput = []
  results_enb = []
  results_enb_std = []
  results_sinr = []
  results_rcvd_packets = []
  results_packets_sent = []
  results_enddelay = []
  value_keys = []

  for n in range(len(csvs)):
    preItervar, preRunattr, preVector, preScalar, extra_info, num_enbs = processInitialData(csvs[n])

    tmp_throughput = get_data_from_vector('throughput:vector', "ue", preVector, num_ues, 1)['vecvalue']
    data_throughput = get_data_vector_mean(tmp_throughput)
    throughput, _, _ = getCOV(data_throughput, extra_info, 'min_snr_used', sliced= True, repetition = preRunattr["repetition"])

    enbs, _, _ = getCOV(num_enbs, extra_info, 'min_snr_used', sliced= True, repetition = preRunattr["repetition"])
    enbs_std, _, _ = getCOV(num_enbs, extra_info, 'min_snr_used', sliced= True, repetition = preRunattr["repetition"], slice_op= 'std')

    data_sinr = get_data_from_scalar("rcvdSinr:mean", "ue", preScalar, num_ues, 1)
    sinr, _, _ = getCOV(data_sinr.fillna(-10), extra_info, 'min_snr_used', sliced= True, repetition = preRunattr["repetition"])
    results_sinr.append(sinr)

    results_throughput.append(throughput)
    results_enb.append(enbs)
    results_enb_std.append(enbs_std)
    results_sinr.append(sinr)

    if extra:
      tmp_enddelay = get_data_from_vector('endToEndDelay:vector', "ue", preVector, num_ues, 1)['vecvalue']
      data_enddelay = get_data_vector_mean(tmp_enddelay)
      enddelay, _, _ = getCOV(data_enddelay, extra_info, 'min_snr_used', sliced= True, repetition = preRunattr["repetition"])

      results_enddelay.append(enddelay)

      data_rcvd_packets = get_data_from_scalar("packetReceived:count", "ue", preScalar, num_ues, 1)
      rcvd_packets, _, _ = getCOV(data_rcvd_packets, extra_info, 'min_snr_used', sliced= True, slice_op= 'sum', repetition = preRunattr["repetition"])

      results_rcvd_packets.append(rcvd_packets)

      data_packets_sent = get_data_from_scalar("packetSent:count", "server", preScalar, num_ues, 1)
      packets_sent, colors, names = getCOV(data_packets_sent, extra_info, 'min_snr_used', sliced= True, slice_op= 'sum', repetition = preRunattr["repetition"])

      results_packets_sent.append(packets_sent)

    tmp_tuple = ()
    for name in dict_ids:
      tmp_tuple += (dict_ids[name][n],)

    value_keys.append(tmp_tuple)

  names = dict_ids.keys()

  all_throughput = pd.concat(results_throughput, keys= value_keys, names= names)
  all_sinr = pd.concat(results_sinr, keys= value_keys, names= names)
  all_enb_mean = pd.concat(results_enb, keys= value_keys, names= names)
  all_enb_std = pd.concat(results_enb_std, keys= value_keys, names= names)
  all_enb = pd.DataFrame({'Mean': all_enb_mean['Mean'], 'Std': all_enb_std['Mean']})

  if extra:
    all_enddelay = pd.concat(results_enddelay, keys= value_keys, names= names)
    all_rcvd_packets = pd.concat(results_rcvd_packets, keys= value_keys, names= names)
    all_packets_sent = pd.concat(results_packets_sent, keys= value_keys, names= names)
    return all_throughput, all_sinr, all_enb, all_enddelay, all_rcvd_packets, all_packets_sent
  else:
    return all_throughput, all_sinr, all_enb

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

    throughput_ul, colors, names = getCOV(data_throughput_ul, extra_info, 'min_snr_used', sliced= True, repetition = preRunattr["repetition"])

    lines = throughput_ul.index.get_level_values("RBs").tolist()

    fig = px.ecdf(throughput_ul, x="Mean", color=colors, labels= {"Mean": "Throughput (bps)", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: UE Throughput UL - CDF", hover_data = ["COV"], ecdfmode="reversed", hover_name = names, line_dash= lines, category_orders={"color": ["5", "10", "15"]})

    fig.show()

    tmp_throughput_dl = get_data_from_vector('throughput:vector', "ue", preVector, num_ues, 1)['vecvalue']
    data_throughput_dl = get_data_vector_mean(tmp_throughput_dl)

    throughput_dl, colors, names = getCOV(data_throughput_dl, extra_info, 'min_snr_used', sliced= True, repetition = preRunattr["repetition"])

    lines = throughput_dl.index.get_level_values("RBs").tolist()

    fig = px.ecdf(throughput_dl, x="Mean", color=colors, labels= {"Mean": "Throughput (bps)", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: UE Throughput DL - CDF", hover_data = ["COV"], hover_name = names, ecdfmode="reversed", line_dash= lines, category_orders={"color": ["5", "10", "15"]})

    fig.show()

    fig = px.ecdf(throughput_dl, x="COV", color=colors, labels= {"Mean": "Throughput (bps)", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: COV UE Throughput DL - CDF", hover_data = ["COV"], hover_name = names, ecdfmode="reversed", line_dash= lines, category_orders={"color": ["5", "10", "15"]})

    fig.show()

    enbs, colors, names = getCOV(num_enbs, extra_info, 'min_snr_used', sliced= True, repetition = preRunattr["repetition"])
    enbs_std, colors, names = getCOV(num_enbs, extra_info, 'min_snr_used', sliced= True, slice_op='std', repetition = preRunattr["repetition"])

    fig = px.bar(enbs, x= colors, y= "Mean", color= colors, labels= {"x" : "Min Snr Used (dB)" ,"color" : "Min Snr Used (dB)", "y": "Mean of Used Enbs"},
                title= "SLICED: Num Enbs Throughput DL - CDF", hover_name = names, error_y = enbs_std["Mean"])
    fig.show()

    """### End To End Delay"""

    tmp_enddelay_dl = get_data_from_vector('endToEndDelay:vector', "ue", preVector, num_ues, 1)['vecvalue']
    data_enddelay_dl = get_data_vector_mean(tmp_enddelay_dl)

    enddelay_dl, colors, names = getCOV(data_enddelay_dl, extra_info, 'min_snr_used', sliced= True, repetition = preRunattr["repetition"])

    lines = enddelay_dl.index.get_level_values("RBs").tolist()

    fig = px.ecdf(enddelay_dl, x="Mean", color=colors, labels= {"Mean": "Delay (s)", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: UE End to End Delay DL - CDF", hover_data = ["COV"], hover_name = names, ecdfmode="reversed", line_dash= lines)

    fig.show()

    tmp_enddelay_ul = get_data_from_vector('endToEndDelay:vector', "server", preVector, num_ues, 1)['vecvalue']
    data_enddelay_ul = get_data_vector_mean(tmp_enddelay_ul)

    enddelay_ul, colors, names = getCOV(data_enddelay_ul, extra_info, 'min_snr_used', sliced= True, repetition = preRunattr["repetition"])

    lines = enddelay_ul.index.get_level_values("RBs").tolist()

    fig = px.ecdf(enddelay_ul, x="Mean", color=colors, labels= {"Mean": "Delay (s)", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: UE End to End Delay UL - CDF", hover_data = ["COV"], hover_name = names, ecdfmode="reversed", line_dash= lines)

    fig.show()

    """### Packets"""

    data_packets_rcvd_ul = get_data_from_scalar("packetReceived:count", "server", preScalar, num_ues, 1)

    ul_packets_rcvd, colors, names = getCOV(data_packets_rcvd_ul, extra_info, 'min_snr_used', sliced= True, slice_op= 'sum', repetition = preRunattr["repetition"])

    lines = ul_packets_rcvd.index.get_level_values("RBs").tolist()

    fig = px.ecdf(ul_packets_rcvd, x="Mean", color=colors, labels= {"Mean": "Packets", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: UE Packets Received UL - CDF", hover_data = ["COV"], hover_name = names,ecdfmode="reversed", line_dash= lines)

    fig.show()

    data_packets_rcvd_ul.isna().sum().sum()

    data_packets_sent_ul = get_data_from_scalar("packetSent:count", "ue", preScalar, num_ues, 1)

    ul_packets_sent, colors, names = getCOV(data_packets_sent_ul, extra_info, 'min_snr_used', sliced= True, slice_op= 'sum', repetition = preRunattr["repetition"])

    lines = ul_packets_sent.index.get_level_values("RBs").tolist()

    fig = px.ecdf(ul_packets_sent, x="Mean", color=colors, labels= {"Mean": "Packets", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: Packets Sent per UE UL - CDF", hover_data = ["COV"], hover_name = names,ecdfmode="reversed", line_dash= lines)

    fig.show()

    data_packets_sent_ul.isna().sum().sum()

    data_packets_dl = get_data_from_scalar("packetReceived:count", "ue", preScalar, num_ues, 1)

    dl_packets, colors, names = getCOV(data_packets_dl, extra_info, 'min_snr_used', sliced= True, slice_op= 'sum', repetition = preRunattr["repetition"])

    lines = dl_packets.index.get_level_values("RBs").tolist()

    fig = px.ecdf(dl_packets, x="Mean", color=colors, labels= {"Mean": "Packets", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: Packets Received per UE DL - CDF", hover_data = ["COV"], hover_name = names,ecdfmode="reversed", line_dash= lines)

    fig.show()

    data_packets_dl.isna().sum().sum()

    data_packets_sent_dl = get_data_from_scalar("packetSent:count", "server", preScalar, num_ues, 1)

    dl_packets_sent, colors, names = getCOV(data_packets_sent_dl, extra_info, 'min_snr_used', sliced= True, slice_op= 'sum', repetition = preRunattr["repetition"])

    lines = dl_packets_sent.index.get_level_values("RBs").tolist()

    fig = px.ecdf(dl_packets_sent, x="Mean", color=colors, labels= {"Mean": "Packets", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: Packets Sent per UE DL - CDF", hover_data = ["COV"], hover_name = names,ecdfmode="reversed", line_dash= lines)

    fig.show()

    data_packets_sent_dl.isna().sum().sum()

    """### PacketsBytes"""

    data_packets_rcvd_ul = get_data_from_scalar("packetReceived:sum(packetBytes)", "server", preScalar, num_ues, 1)

    ul_packets_rcvd, colors, names = getCOV(data_packets_rcvd_ul, extra_info, 'min_snr_used', sliced= True, slice_op= 'sum', repetition = preRunattr["repetition"])

    lines = ul_packets_rcvd.index.get_level_values("RBs").tolist()

    fig = px.ecdf(ul_packets_rcvd, x="Mean", color=colors, labels= {"Mean": "Bytes", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: UE Bytes Received UL - CDF", hover_data = ["COV"], hover_name = names,ecdfmode="reversed", line_dash= lines)

    fig.show()

    data_packets_rcvd_ul.isna().sum().sum()

    data_packets_sent_ul = get_data_from_scalar("packetSent:sum(packetBytes)", "ue", preScalar, num_ues, 1)

    ul_packets_sent, colors, names = getCOV(data_packets_sent_ul, extra_info, 'min_snr_used', sliced= True, slice_op= 'sum', repetition = preRunattr["repetition"])

    lines = ul_packets_sent.index.get_level_values("RBs").tolist()

    fig = px.ecdf(ul_packets_sent, x="Mean", color=colors, labels= {"Mean": "Bytes", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: Bytes Sent per UE UL - CDF", hover_data = ["COV"], hover_name = names,ecdfmode="reversed", line_dash= lines)

    fig.show()

    data_packets_sent_ul.isna().sum().sum()

    data_packets_dl = get_data_from_scalar("packetReceived:sum(packetBytes)", "ue", preScalar, num_ues, 1)

    dl_packets, colors, names = getCOV(data_packets_dl, extra_info, 'min_snr_used', sliced= True, slice_op= 'sum', repetition = preRunattr["repetition"])

    lines = dl_packets.index.get_level_values("RBs").tolist()

    fig = px.ecdf(dl_packets, x="Mean", color=colors, labels= {"Mean": "Bytes", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: Bytes Received per UE DL - CDF", hover_data = ["COV"], hover_name = names,ecdfmode="reversed", line_dash= lines)

    fig.show()

    data_packets_dl.isna().sum().sum()

    data_packets_sent_dl = get_data_from_scalar("packetSent:sum(packetBytes)", "server", preScalar, num_ues, 1)

    dl_packets_sent, colors, names = getCOV(data_packets_sent_dl, extra_info, 'min_snr_used', sliced= True, slice_op= 'sum', repetition = preRunattr["repetition"])

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

    mean_sinr_dl, colors, names = getCOV(data_sinr.fillna(0), extra_info, 'min_snr_used', repetition = preRunattr["repetition"])

    lines = mean_sinr_dl.index.get_level_values("RBs").tolist()

    fig = px.ecdf(mean_sinr_dl, x="Mean", color=colors, labels= {"Mean": "Sinr:Mean (dB)", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: Downlink Sinr per UE - CDF", hover_data = ["COV"], ecdfmode="reversed", hover_name = names, line_dash = lines)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE SNR - VER COMO CONSIDERAR

    fig = px.ecdf(mean_sinr_dl, x="COV", color=colors, labels= {"Mean": "Sinr:Mean (dB)", "color" : "Min Snr Used (dB)", "line_dash": "RBs"}, markers= False, lines= True,
                  title= "SLICED: Downlink Sinr COV per UE - CDF", hover_data = ["Mean"], hover_name = names, line_dash= lines, category_orders={"color": ["5", "10", "15"]})

    fig.show()

    """Sinr: aumentou a largura de banda"""

    mean_sinr_dl, colors, names = getCOV(data_sinr, extra_info, 'min_snr_used', repetition = preRunattr["repetition"])

    dl_thr, colors, names = getCOV(data_throughput_dl, extra_info, 'min_snr_used', dropna = True, repetition = preRunattr["repetition"])

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

    mean_sinr_ul, colors, names = getCOV(mean_rcvdsinr, extra_info, 'min_snr_used', repetition = preRunattr["repetition"])

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

    tmp_data, colors, names = getCOV(dataUL.isna()*100, extra_info, "min_snr_used" , repetition = preRunattr["repetition"])

    tmp_data = tmp_data.replace(0, np.nan).dropna()

    colors = tmp_data.index.get_level_values('min_snr_used').tolist()

    names = tmp_data.index.get_level_values('n_obj').tolist()

    fig = px.bar(tmp_data, x=names, y="Mean", hover_name = names, barmode= "group",
                color=colors, labels= {"Mean": "Percentage of Slices (%)", "x": "Apps", "color": "Min Snr Used (dB)"},
                title= "SLICED: Percentage of times that each UE couldn't connect (UL Throughput)")

    fig.show()

    #CHANGE

    """#### **Throughput results**"""

    ul_thr, colors, names = getCOV(dataUL.fillna(0), extra_info, 'min_snr_used', dropna= True, repetition = preRunattr["repetition"])

    fig = px.ecdf(ul_thr, x='Mean', color = colors, labels= {"Mean": "Throughput:Mean (Bps)", "color": "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Throughput UL per UE - CDF", ecdfmode="reversed", hover_name = names)

    fig.show()

    dl_thr, colors, names = getCOV(dataDL, extra_info, 'min_snr_used', dropna= True, repetition = preRunattr["repetition"])

    fig = px.ecdf(dl_thr, x='Mean', color = colors, labels= {"Mean": "Throughput:Mean (Bps)", "color": "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Throughput DL per UE - CDF", ecdfmode="reversed", hover_name = names)

    fig.show()

    fig = px.ecdf(dl_thr, x='COV', color = colors, labels= {"Mean": "Throughput:Mean (Bps)", "color": "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: COV Throughput DL per UE - CDF", hover_name = names, hover_data= ["Mean"])

    fig.show()

    """#### **Spectral Eficiency**"""

    #Efic Spec = throughput / (bandw * %utilization)

    bandw = 20*10**6

    mean_sinr_dl, colors, names = getCOV(data_sinr, extra_info, 'min_snr_used', repetition = preRunattr["repetition"])

    dl_thr, colors, names = getCOV(dataDL, extra_info, 'min_snr_used', dropna= True, repetition = preRunattr["repetition"])

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

    dl_framedelay, colors, names = getCOV(data_frame_delay_dl, extra_info, 'min_snr_used', repetition = preRunattr["repetition"])

    fig = px.ecdf(dl_framedelay, x="Mean", color=colors, labels= {"Mean": "Delay: Mean (s)", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Frame Delay DL per UE - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ul_framedelay, colors, names = getCOV(data_frame_delay_ul, extra_info, 'min_snr_used', repetition = preRunattr["repetition"])

    fig = px.ecdf(ul_framedelay, x="Mean", color=colors, labels= {"Mean": "Delay: Mean (s)", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Frame Delay UL per UE - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    dl_delay, colors, names = getCOV(data_delay_dl, extra_info, 'min_snr_used', repetition = preRunattr["repetition"])

    fig = px.ecdf(dl_delay, x="Mean", color=colors, labels= {"Mean": "Delay: Mean (s)", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Playout Delay DL per UE - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE TEMPO - VER COMO CONSIDERAR

    ul_delay, colors, names = getCOV(data_delay_ul, extra_info, 'min_snr_used', repetition = preRunattr["repetition"])

    fig = px.ecdf(ul_delay, x="Mean", color=colors, labels= {"Mean": "Delay: Mean (s)", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Playout Delay UL per UE - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE TEMPO - VER COMO CONSIDERAR

    mean_delay, colors, names = getCOV(delay, extra_info, 'min_snr_used', repetition = preRunattr["repetition"])

    fig = px.ecdf(mean_delay, x="Mean", color=colors, labels= {"Mean": "Delay (s)", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  marginal="rug",  title= "SLICED: Playout Delay per UE - CDF", hover_data = ["COV"], hover_name = names)

    #fig.show()

    """**Loss < 1%** 

    Considering: 

    1. Playout Loss => Times jitter > 0

    2. Tail Drop Loss => buffer full

    3. Frame Loss => Channel Loss

    """

    ul_loss, colors, names = getCOV(data_loss_ul, extra_info, 'min_snr_used', repetition = preRunattr["repetition"])

    fig = px.ecdf(ul_loss, x="Mean", color=colors, labels= {"Mean": "Loss rate", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Loss per UE UL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE TEMPO E PERDAS - VER COMO CONSIDERAR

    dl_loss, colors, names = getCOV(data_loss_dl, extra_info, 'min_snr_used', repetition = preRunattr["repetition"])

    fig = px.ecdf(dl_loss, x="Mean", color=colors, labels= {"Mean": "Loss rate", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Loss per UE DL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE TEMPO E PERDAS - VER COMO CONSIDERAR

    ul_frame_loss, colors, names = getCOV(data_frameloss_ul, extra_info, 'min_snr_used', repetition = preRunattr["repetition"])

    fig = px.ecdf(ul_frame_loss, x="Mean", color=colors, labels= {"Mean": "Loss rate", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Frame Loss per UE UL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE TEMPO E PERDAS - VER COMO CONSIDERAR

    dl_frame_loss, colors, names = getCOV(data_frameloss_dl, extra_info, 'min_snr_used', repetition = preRunattr["repetition"])

    fig = px.ecdf(dl_frame_loss, x="Mean", color=colors, labels= {"Mean": "Loss rate", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Frame Loss per UE DL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE TEMPO E PERDAS - VER COMO CONSIDERAR

    dl_tail_loss, colors, names = getCOV(data_tailloss_dl, extra_info, 'min_snr_used', dropna= False, repetition = preRunattr["repetition"])

    fig = px.ecdf(dl_tail_loss, x="Mean", color=colors, labels= {"Mean": "Loss rate", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: TailLoss per UE DL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE TEMPO E PERDAS - VER COMO CONSIDERAR

    ul_tail_loss, colors, names = getCOV(data_tailloss_ul, extra_info, 'min_snr_used', repetition = preRunattr["repetition"])

    fig = px.ecdf(ul_tail_loss, x="Mean", color=colors, labels= {"Mean": "Loss rate", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Tail Loss per UE UL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE TEMPO E PERDAS - VER COMO CONSIDERAR

    dl_play_loss, colors, names = getCOV(data_playloss_dl, extra_info, 'min_snr_used', repetition = preRunattr["repetition"])

    fig = px.ecdf(dl_play_loss, x="Mean", color=colors, labels= {"Mean": "Loss rate", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: PlayoutLoss per UE DL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE TEMPO E PERDAS - VER COMO CONSIDERAR

    ul_play_loss, colors, names = getCOV(data_playloss_ul, extra_info, 'min_snr_used', repetition = preRunattr["repetition"])

    fig = px.ecdf(ul_play_loss, x="Mean", color=colors, labels= {"Mean": "Loss rate", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: PlayoutLoss per UE UL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE TEMPO E PERDAS - VER COMO CONSIDERAR

    loss_dl = gen_ues_data_single(data_frameloss_dl, num_ues, directions) + gen_ues_data_single(data_playloss_dl, num_ues, directions) + gen_ues_data_single(data_tailloss_dl, num_ues, directions)

    mean_loss_dl, colors, names = getCOV(loss_dl, extra_info, 'min_snr_used', repetition = preRunattr["repetition"])

    fig = px.ecdf(mean_loss_dl, x="Mean", color=colors, labels= {"Mean": "Loss rate", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Total Loss per UE DL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    loss_ul = gen_ues_data_single(data_frameloss_ul, num_ues, directions) + gen_ues_data_single(data_playloss_ul, num_ues, directions) + gen_ues_data_single(data_tailloss_ul, num_ues, directions)

    mean_loss_ul, colors, names = getCOV(loss_ul, extra_info, 'min_snr_used', repetition = preRunattr["repetition"])

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

    mean_jitter, colors, names = getCOV(jitter, extra_info, 'min_snr_used', repetition = preRunattr["repetition"])

    fig = px.ecdf(mean_jitter, x="Mean", color=colors, labels= {"Mean": "Jitter (s)", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  marginal="rug", title= "SLICED: Jitter per UE - CDF", hover_data = ["COV"], hover_name = names)

    #fig.show()

    dl_jitter, colors, names = getCOV(data_jitter_dl.fillna(0), extra_info, 'min_snr_used', repetition = preRunattr["repetition"])

    fig = px.ecdf(dl_jitter, x="Mean", color=colors, labels= {"Mean": "Jitter (s)", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Jitter per UE DL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE TEMPO E PERDAS - VER COMO CONSIDERAR
    # No caso substituido por 0 pois não existe NaN no throughput, entao os NaN restantes são 0 .

    thr_tmp = gen_ues_data_single(dataUL, num_ues, directions)
    jul_tmp = gen_ues_data_single(data_jitter_ul, num_ues, directions)

    tmp_data_jitter_ul = thr_tmp.notna().replace(False, np.nan).replace(True, 1) * jul_tmp.fillna(0)

    ul_jitter, colors, names = getCOV(tmp_data_jitter_ul, extra_info, 'min_snr_used', dropna= False, repetition = preRunattr["repetition"])

    fig = px.ecdf(ul_jitter, x="Mean", color=colors, labels= {"Mean": "Jitter (s)", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: Jitter per UE UL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DAS MEDIDAS DE TEMPO E PERDAS - VER COMO CONSIDERAR

    """**MOS:**"""

    dl_mos, colors, names = getCOV(data_mos_dl, extra_info, 'min_snr_used', repetition = preRunattr["repetition"])

    fig = px.ecdf(dl_mos, x="Mean", color=colors, labels= {"Mean": "MOS", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: MOS per UE DL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DE MOS - CONSIDERAR COMO 1 (PIOR NOTA)?

    fig = px.ecdf(dl_mos, x="COV", color=colors, labels= {"Mean": "MOS", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: MOS COV per UE DL - CDF", hover_data = ["Mean"], hover_name = names)

    fig.show()

    ul_mos, colors, names = getCOV(data_mos_ul.fillna(1), extra_info, 'min_snr_used', repetition = preRunattr["repetition"])

    fig = px.ecdf(ul_mos, x="Mean", color=colors, labels= {"Mean": "MOS", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: MOS per UE UL - CDF", hover_data = ["COV"], hover_name = names)

    fig.show()

    ######## IMPORTANTE: LEMBRAR DE MUDAR PARA NÃO CONSIDERAR NAN COMO 0 NOS CASOS DE MOS - CONSIDERAR COMO 1 (PIOR NOTA)?

    fig = px.ecdf(ul_mos, x="COV", color=colors, labels= {"Mean": "MOS", "color" : "Min Snr Used (dB)"}, markers= False, lines= True,
                  title= "SLICED: MOS COV per UE UL - CDF", hover_data = ["Mean"], hover_name = names)

    fig.show()
      
def comparing_video(num_ues= 60):
  """## **Comparing**"""

  fixed_30dbm_123 = pd.read_csv('C:/Curso/CCOpMv/VBox/chosen_seed_123/micro_power_30/ilp_fixed_sliced_video.csv')
  fixed_40dbm_123 = pd.read_csv('C:/Curso/CCOpMv/VBox/chosen_seed_123/micro_power_40/ilp_fixed_sliced_video.csv')
  varying_30dbm_123 = pd.read_csv('C:/Curso/CCOpMv/VBox/chosen_seed_123/micro_power_30/ilp_varying_sliced_video.csv')
  varying_40dbm_123 = pd.read_csv('C:/Curso/CCOpMv/VBox/chosen_seed_123/micro_power_40/ilp_varying_sliced_video.csv')

  fixed_20dbm_213 = pd.read_csv('C:/Curso/CCOpMv/VBox/chosen_seed_213/micro_power_20/ilp_fixed_sliced_video.csv')
  fixed_20dbm_321 = pd.read_csv('C:/Curso/CCOpMv/VBox/chosen_seed_321/micro_power_20/ilp_fixed_sliced_video.csv')
  fixed_40dbm_321 = pd.read_csv('C:/Curso/CCOpMv/VBox/chosen_seed_321/micro_power_40/ilp_fixed_sliced_video.csv')

  #fixed_30dbm_25 = pd.read_csv('C:/Curso/CCOpMv/VBox/etc/ilp_fixed_sliced_video_123_25.csv')
  #fixed_30dbm_50 = pd.read_csv('C:/Curso/CCOpMv/VBox/etc/ilp_fixed_sliced_video_213_50.csv')

  images_dir = "Images/"

  """### Fixed x Varying (Same seed, power 30 dBm)"""

  all_throughput, all_sinr, all_enb, all_enddelay, all_rcvd_packets, all_packets_sent = compare_csvs_video([fixed_30dbm_123, varying_30dbm_123], {'ILP' : ['Fixed', 'Varying'], 'Power': [30, 30]}, num_ues, extra= True)

  colors = all_throughput.index.get_level_values("min_snr_used").tolist()

  names = all_throughput.index.get_level_values('n_obj').tolist()

  lines = all_throughput.index.get_level_values("ILP").tolist()

  facet = all_throughput.index.get_level_values("Power").tolist()

  fig = px.ecdf(all_throughput, x='Mean', color = colors, labels= {"Mean": "Throughput:Mean (Bps)", "color": "Min Snr Used (dB)", "line_dash": "ILP Type", "facet_col": "Power"}, markers= False, lines= True,
                title= "UEs Throughput DL - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

  fig.write_image(images_dir+"thr_fixedxvarying.svg")

  fig = px.ecdf(all_throughput, x='COV', color = colors, labels= {"COV": "Throughput:Mean COV", "color": "Min Snr Used (dB)", "line_dash": "ILP Type", "facet_col": "Power"}, markers= False, lines= True,
                title= "UEs Throughput COV DL - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

  fig.write_image(images_dir+"thr_fixedxvarying_cov.svg")

  #median_data = tmp_thr.groupby(["min_snr_used", "ILP", "RBs"], dropna = False).median()

  colors = all_enb.index.get_level_values("min_snr_used").tolist()

  names = all_enb.index.get_level_values('n_obj').tolist()

  shape = all_enb.index.get_level_values("ILP").tolist()

  facet = all_enb.index.get_level_values("Power").tolist()

  fig = px.bar(all_enb, x= colors, y= "Mean", color= colors, labels= {"x" : "Min Snr Used (dB)" ,"color" : "ILP Type", "Mean": "Mean of Used Enbs", "facet_col": "Power", "pattern_shape": "ILP Type"},
              title= "Num Enbs per Slice", hover_name = names, error_y = "Std", pattern_shape= shape, barmode = 'group', facet_col= facet, category_orders={"color": ["5", "10", "15"]})

  fig.write_image(images_dir+"enb_fixedxvarying_cov.svg")

  sp = np.sqrt(((30-1)*0.9660918**2 + (30-1)*0.8164966**2)/(30+30-2))
  t = (3.4 - 3)/(sp * np.sqrt(2/30))
  #print(t)

  colors = all_sinr.index.get_level_values("min_snr_used").tolist()

  names = all_sinr.index.get_level_values('n_obj').tolist()

  lines = all_sinr.index.get_level_values("ILP").tolist()

  facet = all_sinr.index.get_level_values("Power").tolist()

  fig = px.ecdf(all_sinr, x='Mean', color = colors, labels= {"Mean": "Sinr:Mean (dB)", "color": "Min Snr Used (dB)", "line_dash": "ILP Type", "facet_col": "Power"}, markers= False, lines= True,
                title= "UE Sinr DL - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

  fig.write_image(images_dir+"sinr_fixedxvarying.svg")

  fig = px.ecdf(all_sinr, x='COV', color = colors, labels= {"COV": "Sinr:Mean COV", "color": "Min Snr Used (dB)", "line_dash": "ILP Type", "facet_col": "Power"}, markers= False, lines= True,
                title= "UE Sinr DL COV - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

  fig.write_image(images_dir+"sinr_fixedxvarying_cov.svg")

  colors = all_enddelay.index.get_level_values("min_snr_used").tolist()

  names = all_enddelay.index.get_level_values('n_obj').tolist()

  lines = all_enddelay.index.get_level_values("ILP").tolist()

  facet = all_enddelay.index.get_level_values("Power").tolist()

  fig = px.ecdf(all_enddelay, x='Mean', color = colors, labels= {"Mean": "Delay (s)", "color": "Min Snr Used (dB)", "line_dash": "ILP Type", "facet_col": "Power"}, markers= False, lines= True,
                title= "End to End Delay of each UE DL - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

  fig.write_image(images_dir+"edd_fixedxvarying.svg")

  fig = px.ecdf(all_enddelay, x='COV', color = colors, labels= {"COV": "COV", "color": "Min Snr Used (dB)", "line_dash": "ILP Type", "facet_col": "Power"}, markers= False, lines= True,
                title= "End to End Delay COV of each UE DL - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

  fig.write_image(images_dir+"edd_fixedxvarying_cov.svg")

  colors = all_rcvd_packets.index.get_level_values("min_snr_used").tolist()

  names = all_rcvd_packets.index.get_level_values('n_obj').tolist()

  lines = all_rcvd_packets.index.get_level_values("ILP").tolist()

  facet = all_rcvd_packets.index.get_level_values("Power").tolist()

  fig = px.ecdf(all_rcvd_packets, x='Mean', color = colors, labels= {"Mean": "Number of Received Packets", "color": "Min Snr Used (dB)", "line_dash": "ILP Type", "facet_col": "Power"}, markers= False, lines= True,
                title= "Received packets by each UE DL - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

  fig.write_image(images_dir+"rcvdpkt_fixedxvarying.svg")

  colors = all_packets_sent.index.get_level_values("min_snr_used").tolist()

  names = all_packets_sent.index.get_level_values('n_obj').tolist()

  lines = all_packets_sent.index.get_level_values("ILP").tolist()

  facet = all_packets_sent.index.get_level_values("Power").tolist()

  fig = px.ecdf(all_packets_sent, x='Mean', color = colors, labels= {"Mean": "Number of Packets Sent", "color": "Min Snr Used (dB)", "line_dash": "ILP Type", "facet_col": "Power"}, markers= False, lines= True,
                title= "Packets sent to each UE DL - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

  fig.write_image(images_dir+"pktsent_fixedxvarying.svg")

  """### Power 30 dBm x Power 40 dBm"""

  #tmp_throughput_dl_varying_40 = get_data_from_vector('throughput:vector', "ue", preVecDataVarying40, num_ues, 1)['vecvalue']
  #data_throughput_dl_varying_40 = get_data_vector_mean(tmp_throughput_dl_varying_40)

  #throughput_dl_varying_40, colors, names = getCOV(data_throughput_dl_varying_40, extra_info_varying_40, 'min_snr_used', sliced= True, repetition = preRunattrVarying40["repetition"])

  #tmp_thr = pd.concat([throughput_dl, throughput_dl_varying_40], keys= [30, 40], names = ["Power"])

  all_throughput, all_sinr, all_enb, all_enddelay, all_rcvd_packets, all_packets_sent = compare_csvs_video([varying_40dbm_123, varying_30dbm_123], {'ILP' : ['Varying', 'Varying'], 'Power': [40, 30]}, num_ues, extra= True)

  colors = all_throughput.index.get_level_values("min_snr_used").tolist()

  names = all_throughput.index.get_level_values('n_obj').tolist()

  lines = all_throughput.index.get_level_values("Power").tolist()

  facet = all_throughput.index.get_level_values("RBs").tolist()

  fig = px.ecdf(all_throughput, x='Mean', color = colors, labels= {"Mean": "Throughput:Mean (Bps)", "color": "Min Snr Used (dB)", "line_dash": "Transmission Power (dBm)", "facet_col": "RBs"}, markers= False, lines= True,
                title= "Sliced: UE Throughput Varying DL - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

  fig.write_image(images_dir+"thr_30x40_varying.svg")

  fig = px.ecdf(all_throughput, x='COV', color = colors, labels= {"COV": "Throughput:Mean COV", "color": "Min Snr Used (dB)", "line_dash": "Transmission Power (dBm)", "facet_col": "RBs"}, markers= False, lines= True,
                title= "Sliced: UE Throughput Varying DL COV - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

  fig.write_image(images_dir+"thr_30x40_varying_cov.svg")

  colors = all_enb.index.get_level_values("min_snr_used").tolist()

  names = all_enb.index.get_level_values('n_obj').tolist()

  shape = all_enb.index.get_level_values("Power").tolist()

  facet = all_enb.index.get_level_values("RBs").tolist()

  #median_data = tmp_thr.groupby(["min_snr_used", "ILP", "RBs"], dropna = False).median()

  fig = px.bar(all_enb, x= colors, y= "Mean", color= colors, labels= {"x" : "Min Snr Used (dB)" ,"color" : "Transmission Power (dBm)", "Mean": "Mean of Used Enbs", "facet_col": "RBs", "pattern_shape": "Transmission Power (dBm)"},
              title= "SLICED: Num Enbs Varying", hover_name = names, error_y = "Std", pattern_shape= shape, barmode = 'group', facet_col= facet, category_orders={"color": ["5", "10", "15"]})
  fig.write_image(images_dir+"enb_30x40_varying.svg")

  all_throughput_fixed, all_sinr_fixed, all_enb_fixed, all_enddelay_fixed, all_rcvd_packets_fixed, all_packets_sent_fixed = compare_csvs_video([fixed_40dbm_123, fixed_30dbm_123], {'ILP' : ['Fixed', 'Fixed'], 'Power': [40, 30]}, num_ues, extra= True)

  colors = all_throughput_fixed.index.get_level_values("min_snr_used").tolist()

  names = all_throughput_fixed.index.get_level_values('n_obj').tolist()

  lines = all_throughput_fixed.index.get_level_values("Power").tolist()

  facet = all_throughput_fixed.index.get_level_values("RBs").tolist()

  fig = px.ecdf(all_throughput_fixed, x='Mean', color = colors, labels= {"Mean": "Throughput:Mean (Bps)", "color": "Min Snr Used (dB)", "line_dash": "Transmission Power (dBm)", "facet_col": "RBs"}, markers= False, lines= True,
                title= "Sliced: UE Throughput Fixed DL - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

  fig.write_image(images_dir+"thr_30x40_fixed.svg")

  fig = px.ecdf(all_throughput_fixed, x='COV', color = colors, labels= {"COV": "Throughput:Mean COV", "color": "Min Snr Used (dB)", "line_dash": "Transmission Power (dBm)", "facet_col": "RBs"}, markers= False, lines= True,
                title= "Sliced: UE Throughput Fixed DL COV - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

  fig.write_image(images_dir+"thr_30x40_fixed_cov.svg")

  colors = all_enb_fixed.index.get_level_values("min_snr_used").tolist()

  names = all_enb_fixed.index.get_level_values('n_obj').tolist()

  shape = all_enb_fixed.index.get_level_values("Power").tolist()

  facet = all_enb_fixed.index.get_level_values("RBs").tolist()

  #median_data = tmp_thr.groupby(["min_snr_used", "ILP", "RBs"], dropna = False).median()

  fig = px.bar(all_enb_fixed, x= colors, y= "Mean", color= colors, labels= {"x" : "Min Snr Used (dB)" , "Mean": "Mean of Used Enbs", "color":"Transmission Power (dBm)", "facet_col": "RBs", "pattern_shape": "Transmission Power (dBm)"},
              title= "SLICED: Num Enbs Fixed", hover_name = names, error_y = "Std", pattern_shape= shape, barmode = 'group', facet_col= facet, category_orders={"color": ["5", "10", "15"]})

  fig.write_image(images_dir+"enb_30x40_fixed.svg")

  """#### Extra"""

  colors = all_sinr.index.get_level_values("min_snr_used").tolist()

  names = all_sinr.index.get_level_values('n_obj').tolist()

  lines = all_sinr.index.get_level_values("Power").tolist()

  facet = all_sinr.index.get_level_values("RBs").tolist()

  fig = px.ecdf(all_sinr, x='Mean', color = colors, labels= {"Mean": "Sinr:Mean (dB)", "color": "Min Snr Used (dB)", "line_dash": "Transmission Power (dBm)", "facet_col": "RBs"}, markers= False, lines= True,
                title= "Sliced: UE Sinr Varying DL - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

  fig.write_image(images_dir+"sinr_30x40_varying.svg")

  fig = px.ecdf(all_sinr, x='COV', color = colors, labels= {"COV": "Sinr:Mean COV", "color": "Min Snr Used (dB)", "line_dash": "Transmission Power (dBm)", "facet_col": "RBs"}, markers= False, lines= True,
                title= "Sliced: UE Sinr DL Varying COV - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

  fig.write_image(images_dir+"sinr_30x40_varying_cov.svg")

  colors = all_sinr_fixed.index.get_level_values("min_snr_used").tolist()

  names = all_sinr_fixed.index.get_level_values('n_obj').tolist()

  lines = all_sinr_fixed.index.get_level_values("Power").tolist()

  facet = all_sinr_fixed.index.get_level_values("RBs").tolist()

  fig = px.ecdf(all_sinr_fixed, x='Mean', color = colors, labels= {"Mean": "Sinr:Mean (dB)", "color": "Min Snr Used (dB)", "line_dash": "Transmission Power (dBm)", "facet_col": "RBs"}, markers= False, lines= True,
                title= "Sliced: UE Sinr Fixed DL - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

  fig.write_image(images_dir+"sinr_30x40_fixed.svg")

  fig = px.ecdf(all_sinr_fixed, x='COV', color = colors, labels= {"COV": "Sinr:Mean COV", "color": "Min Snr Used (dB)", "line_dash": "Transmission Power (dBm)", "facet_col": "RBs"}, markers= False, lines= True,
                title= "Sliced: UE Sinr DL Fixed COV - CDF", ecdfmode="reversed", hover_name = names, line_dash= lines, facet_col= facet, category_orders={"color": ["5", "10", "15"]})

  fig.write_image(images_dir+"sinr_30x40_fixed_cov.svg")

  """### Seeds (321, 213)


  """

  all_throughput_seeds, all_sinr_seeds, all_enb_seeds, all_enddelay_seeds, all_rcvd_packets_seeds, all_packets_sent_seeds = compare_csvs_video([fixed_20dbm_213, fixed_20dbm_321, fixed_40dbm_321, fixed_40dbm_123], {'ILP' : ['Fixed', 'Fixed', 'Fixed', 'Fixed'], 'Power': [20, 20, 40, 40], 'Seed': [213, 321, 321, 123]}, num_ues, extra= True)

  msu = all_throughput_seeds.index.get_level_values("min_snr_used").tolist()

  names = all_throughput_seeds.index.get_level_values('n_obj').tolist()

  power = all_throughput_seeds.index.get_level_values("Power").tolist()

  ilp = all_throughput_seeds.index.get_level_values("ILP").tolist()

  seed = all_throughput_seeds.index.get_level_values("Seed").tolist()

  fig = px.ecdf(all_throughput_seeds, x='Mean', color = msu, labels= {"Mean": "Throughput:Mean (Bps)", "color": "Min Snr Used (dB)", "line_dash": "Power (dBm)", "facet_col": "ILP Type"}, markers= False, lines= True,
                title= "UE Throughput Fixed DL - CDF", ecdfmode="reversed", hover_name = names, line_dash= power, facet_col= ilp, category_orders={"color": ["5", "10", "15"]})

  fig.write_image(images_dir+"thr_seeds_fixed.svg")

  fig = px.ecdf(all_throughput_seeds, x='Mean', color = seed, labels= {"Mean": "Throughput:Mean (Bps)", "color": "Seed used", "facet_row": "Power (dBm)", "facet_col": "Min Snr Used (dB)"}, markers= True, lines= False,
                title= "UE Throughput Fixed DL - CDF", ecdfmode="reversed", hover_name = names, facet_col= msu, category_orders={"color": ["123", "321", "213"]}, facet_row= power)

  fig.write_image(images_dir+"thr_seeds_fixed_2.svg")

  new_all_enb_seeds = propagate_std(all_enb_seeds, "Seed")

  colors = new_all_enb_seeds.index.get_level_values("min_snr_used").tolist()

  names = new_all_enb_seeds.index.get_level_values('n_obj').tolist()

  facet = new_all_enb_seeds.index.get_level_values("ILP").tolist()

  shape = new_all_enb_seeds.index.get_level_values("Power").tolist()

  fig = px.bar(new_all_enb_seeds, x= colors, y= "Mean", color= colors, labels= {"x" : "Min Snr Used (dB)" ,"color" : "Power (dBm)", "Mean": "Mean of Used Enbs", "facet_col": "ILP Type", "pattern_shape": "Power"},
              title= "Num Enbs per Slice", hover_name = names, error_y = "Std", pattern_shape= shape, barmode = 'group', facet_col= facet, category_orders={"color": ["5", "10", "15"]})
  
  fig.write_image(images_dir+"enb_seeds_fixed.svg")

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

  dl_thr_PS, colorsPS, namesPS = getCOV(dataDLPS, extra_info_ps, 'min_snr_used', True, sliced= True, repetition = preRunattrPS["repetition"])

  dl_thr, colors, names = getCOV(dataDL, extra_info, 'min_snr_used', True, sliced= True, repetition = preRunattr["repetition"])

  tmp_thr = pd.concat([dl_thr, dl_thr_PS], keys= [40, 100], names = ["PS"])

  colors = tmp_thr.index.get_level_values("min_snr_used").tolist()

  names = tmp_thr.index.get_level_values('n_obj').tolist()

  symbols = tmp_thr.index.get_level_values("PS").tolist()

  fig = px.ecdf(tmp_thr, x='Mean', color = colors, labels= {"Mean": "Throughput:Mean (Bps)", "color": "Min Snr Used (dB)", "line_dash": "Package Size"}, markers= False, lines= True,
                title= "HANDO: Throughput DL per UE - CDF", ecdfmode="reversed", hover_name = names, line_dash= symbols)

  fig.show()

if __name__ == "__main__":
  comparing_video()