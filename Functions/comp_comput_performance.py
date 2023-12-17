import general_functions as genf
import re
import pandas as pd
import os
import plotly.graph_objects as go


def comparing_performance(chosen_seeds, min_sinr, solutions_dir, modes, extra_dir, **kwargs):
    for param in extra_dir:
        solutions_dir += '/' + (f'{param}_{kwargs[param]}' if param in kwargs else '')

    csvs_info = {}
    
    df = pd.DataFrame(index=[], columns=['mode','seed','min_snr', 'num_vehicle', 'run_time'])
    i = 0
    for mode in modes:
        print(mode)
        csvs_info[mode] = []
        for chosen_seed in chosen_seeds:
            solutions_dir_full = solutions_dir + f'/chosen_seed_{chosen_seed}/logs/'
            
            for _min_sinr in min_sinr:
                with open(solutions_dir_full + f"ilp_{mode}_sliced_{_min_sinr}.log") as file:
                    for line in file:
                        if "carros" in line:
                            print (f"Modo {mode}, seed {chosen_seed}, in line {line}")
                            num_vehicles = re.search(r'\d+\.\d+', line).group()
                        elif "hours" in line:
                            run_time = re.search(r'\d+\.\d+', line).group()                             

                df.loc[i] = [mode, chosen_seed, _min_sinr, float(num_vehicles), float(run_time)*60]   
                i += 1
        
    df_min_sinr_5 = df[df['min_snr'] == 5]
    df_min_sinr_10 = df[df['min_snr'] == 10]
    df_min_sinr_15 = df[df['min_snr'] == 15]

    df_mode_ga = df[df['mode'] == "ga"]
    df_mode_fixed = df[df['mode'] == "fixed"]
    df_mode_single = df[df['mode'] == "single"]
    df_mode_pgwo2 = df[df['mode'] == "pgwo2"]
    df_mode_pgwo3 = df[df['mode'] == "pgwo3"]

    df_seed_ = [None]*11
    for i in range(len(chosen_seeds)):
        df_seed_[i] = df[df['seed'] == chosen_seeds[i]]
        dbg = df_seed_[i]

    print("min_SNR 5")
    df_min_sinr_5_fixed = df_min_sinr_5[df_min_sinr_5['mode'] == 'fixed']
    df_min_sinr_5_ga = df_min_sinr_5[df_min_sinr_5['mode'] == 'ga']
    df_min_sinr_5_pgwo2 = df_min_sinr_5[df_min_sinr_5['mode'] == 'pgwo2']
    df_min_sinr_5_pgwo3 = df_min_sinr_5[df_min_sinr_5['mode'] == 'pgwo3']
    print("\tFixed: viaturas (média)", df_min_sinr_5_fixed['num_vehicle'].mean())
    print("\tGA: viaturas (média)", df_min_sinr_5_ga['num_vehicle'].mean())
    print("\tPGWO2: viaturas (média)", df_min_sinr_5_pgwo2['num_vehicle'].mean())
    print("\tPGWO3: viaturas (média)", df_min_sinr_5_pgwo3['num_vehicle'].mean())
    print("\n\tFixed: tempo (min média)", df_min_sinr_5_fixed['run_time'].mean())
    print("\tGA: tempo (min média)", df_min_sinr_5_ga['run_time'].mean())
    print("\tPGWO2: tempo (min média)", df_min_sinr_5_pgwo2['run_time'].mean())
    print("\tPGWO3: tempo (min média)", df_min_sinr_5_pgwo3['run_time'].mean())
    print("\n")
    
    print("min_SNR 10")
    df_min_sinr_10_fixed = df_min_sinr_10[df_min_sinr_10['mode'] == 'fixed']
    df_min_sinr_10_ga = df_min_sinr_10[df_min_sinr_10['mode'] == 'ga']
    df_min_sinr_10_pgwo2 = df_min_sinr_10[df_min_sinr_10['mode'] == 'pgwo2']
    df_min_sinr_10_pgwo3 = df_min_sinr_10[df_min_sinr_10['mode'] == 'pgwo3']
    print("\tFixed: viaturas (média)", df_min_sinr_10_fixed['num_vehicle'].mean())
    print("\tGA: viaturas (média)", df_min_sinr_10_ga['num_vehicle'].mean())
    print("\tPGWO2: viaturas (média)", df_min_sinr_10_pgwo2['num_vehicle'].mean())
    print("\tPGWO3: viaturas (média)", df_min_sinr_10_pgwo3['num_vehicle'].mean())
    print("\n\tFixed: tempo (min média)", df_min_sinr_10_fixed['run_time'].mean())
    print("\tGA: tempo (min média)", df_min_sinr_10_ga['run_time'].mean())
    print("\tPGWO2: tempo (min média)", df_min_sinr_10_pgwo2['run_time'].mean())
    print("\tPGWO3: tempo (min média)", df_min_sinr_10_pgwo3['run_time'].mean())
    print("\n")
    
    print("min_SNR 15")
    df_min_sinr_15_fixed = df_min_sinr_15[df_min_sinr_15['mode'] == 'fixed']
    df_min_sinr_15_ga = df_min_sinr_15[df_min_sinr_15['mode'] == 'ga']
    df_min_sinr_15_pgwo2 = df_min_sinr_15[df_min_sinr_15['mode'] == 'pgwo2']
    df_min_sinr_15_pgwo3 = df_min_sinr_15[df_min_sinr_15['mode'] == 'pgwo3']
    print("\tFixed: viaturas (média)", df_min_sinr_15_fixed['num_vehicle'].mean())
    print("\tGA: viaturas (média)", df_min_sinr_15_ga['num_vehicle'].mean())
    print("\tPGWO2: viaturas (média)", df_min_sinr_15_pgwo2['num_vehicle'].mean())
    print("\tPGWO3: viaturas (média)", df_min_sinr_15_pgwo3['num_vehicle'].mean())
    print("\n\tFixed: tempo (min média)", df_min_sinr_15_fixed['run_time'].mean())
    print("\tGA: tempo (min média)", df_min_sinr_15_ga['run_time'].mean())
    print("\tPGWO2: tempo (min média)", df_min_sinr_15_pgwo2['run_time'].mean())
    print("\tPGWO3: tempo (min média)", df_min_sinr_15_pgwo3['run_time'].mean())

    bar1 = [
        df_min_sinr_5_fixed['run_time'].mean(),
        df_min_sinr_5_ga['run_time'].mean(),
        df_min_sinr_5_pgwo2['run_time'].mean(),
        df_min_sinr_5_pgwo3['run_time'].mean()
    ]


    bar2 = [
        df_min_sinr_10_fixed['run_time'].mean(),
        df_min_sinr_10_ga['run_time'].mean(),
        df_min_sinr_10_pgwo2['run_time'].mean(),
        df_min_sinr_10_pgwo3['run_time'].mean()
    ]

    bar3 = [
        df_min_sinr_15_fixed['run_time'].mean(),
        df_min_sinr_15_ga['run_time'].mean(),
        df_min_sinr_15_pgwo2['run_time'].mean(),
        df_min_sinr_15_pgwo3['run_time'].mean()
    ]

    categorias = ['snr 5', 'snr 10', 'snr 15']
    subcategorias = ['AID', 'ga', 'pgwo2', 'pgwo3',]
    valores_medios = [
        bar1,      # 5
        bar2,   # 10
        bar3    # 15
    ]
    cores = ['blue', 'green', 'red', 'orange']

    # Criando os objetos de barras agrupadas
    barras = []
    for i, categoria in enumerate(categorias):
        for j, subcategoria in enumerate(subcategorias):
            barra = go.Bar(
                x=[categoria],
                y=[valores_medios[i][j]],
                name=subcategoria,
                marker=dict(color=cores[j])
            )
            barras.append(barra)

    # Criando o layout do gráfico
    layout = go.Layout(
        title='Gráfico de Barras Agrupadas',
        xaxis=dict(title='Categorias'),
        yaxis=dict(title='Valores Médios'),
        barmode='group'
    )

    # Criando a figura do gráfico
    fig = go.Figure(data=barras, layout=layout)

    # Exibindo o gráfico
    fig.show()

    

if __name__ == "__main__":
    os.chdir("/home/juliano/Documentos/LTE-Scenarios-Simulation/Functions")
    chosen_seeds = [2,6,10,12,13,14,15,21,22,24,25]
    min_sinr = [5,10,15]
    modes = ["ga", "pgwo2", "single"]#, "single"]
    extra_dir = ['disaster_percentage','micro_power']
    disaster_percentage = 0
    micro_power = 30
    solutions_dir = 'Solutions'
    project_dir = '../Network_CCOpMv'
    csv_dir = '_5G/results'

    modes = genf.verify_modes(modes)

    kwargs = {'disaster_percentage': disaster_percentage, 'micro_power': micro_power}

    comparing_performance(chosen_seeds, min_sinr, solutions_dir, modes, extra_dir, **kwargs)