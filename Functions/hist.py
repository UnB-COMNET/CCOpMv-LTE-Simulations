"""import plotly.graph_objects as go
import plotly.io as pio
# Dados para o eixo x e y
x = list(range(1, 13))
y = [28, 56, 91, 122, 151, 184, 155, 126, 102, 73, 41, 12]

# Criação do gráfico
fig = go.Figure(data=[go.Bar(x=x, y=y)])


# Configuração dos eixos e legendas
fig.update_layout(xaxis=dict(title=dict(text='Fatia de tempo', font=dict(size=26))), yaxis_title=dict(text='Quantidade de usuários', font=dict(size=26)))

#Exportando gráfico como svg
pio.write_image(fig, 'graph.svg', format='svg')"""

from cProfile import label
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors

# Cria a matriz
matrix = np.random.rand(10, 10)

matrix[0]=[ 4.25296454 , 9.29804208, -0.19599584 , 2.35003262 ,11.9337498 ,  3.13889362, -0.42586835, -6.91402305 ,-0.65272233, -7.53740016]
matrix[1]=[ 7.84225387,  7.04979176 ,12.99117803 ,15.3328186,   4.52610241 , 7.58187297 , 0.2903117,   0.97196917, -1.60811942, -7.86676588]
matrix[2]=[10.73685836 ,10.95729252 ,12.17101597 ,16.75285086, 16.70287539 , 1.39448069 , 8.50456347,  0.06599887 , 2.10493192, -0.2416317 ]
matrix[3]=[15.37873153 ,23.14657408 ,33.60409595 ,25.50331537 ,19.46045446 ,12.72069711 ,11.41406224 , 0.3020746  , 0.48880108 , 2.64781579]
matrix[4]=[20.30758346 ,37.24746638 ,84.13557111 ,30.04016728 ,20.19679238 ,16.76174208 , 2.70474696 ,-4.4311843 , -3.34013843 ,-2.92467308]
matrix[5]=[16.54497147 ,17.76122989 ,28.23448526 ,29.5047156  ,15.42505504 , 6.5101754 ,-0.12348212  ,2.55403944 , 5.42214557, -1.89977381]
matrix[6]=[ 2.04376686 ,12.51922612 ,21.33617254, 25.27492096 ,11.84163452 , 5.71243883 , 5.2837116  ,-6.41190007, -0.59880965, -1.48567327]
matrix[7]=[  9.21123595 , 11.35645069  , 9.70145666 , 21.67329287 ,14.62409835,   4.31150746   ,9.00825697   ,3.33465152  , 4.75056852 ,-13.61100721]
matrix[8]=[16.00056388 ,10.62737726,  3.33514948, 13.53929348 , 6.74962809,  5.97633051, -0.09838331, -2.80711148, -7.7751503 , -6.51306897]
matrix[9]=[ 5.33371672 ,-1.30842099 , 4.76022014,  7.61692151, -2.03555352 , 3.74816029, -2.247901  , -1.66591007, -5.67467982 ,-0.56659947]


# Cria a figura e o eixo
fig, ax = plt.subplots()

# Cria a lista de cores e posições
color = [[0.0, 'violet'], [0.10, 'blue'], [0.20, 'green'], [0.25, 'yellow'], [0.50, 'orange'], [1.0, 'red']]

# Cria o mapa de cores
cmap = colors.LinearSegmentedColormap.from_list("teste", color)

# Exibe a matriz com um gradiente de cores
im = ax.imshow(matrix,extent=[0, 4000, 4000, 0], cmap=cmap)

# Adiciona a barra de cores
cbar  = fig.colorbar(im, label="SNR previsto (dB)")
cbar.ax.xaxis.set_ticks_position('top')

# Move os rótulos do eixo x para cima
ax.xaxis.tick_top()

xmin, xmax = ax.get_xlim()
ymin, ymax = ax.get_ylim()
for i in range(matrix.shape[0]):
    for j in range(matrix.shape[1]):
        x = xmin + (j / matrix.shape[1]) * (xmax - xmin)
        y = ymin + (i / matrix.shape[0]) * (ymax - ymin)
        print(i, j, x, y)
        ax.text(x, y, str(matrix[i, j]), ha='center', va='center', color='w',bbox=dict(facecolor='gray', alpha=0.5))



# Exibe a figura
plt.show()

