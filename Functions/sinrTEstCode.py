from math import ceil, sin
import sinr_comput as sc
import coordinates as coor

file_name = "sinrTestCode.txt"

repetition = 10
sinrMap = [[0 for _ in range(10)] for _ in range(10)]

k = 0 
j = 0
with open(file_name, 'w') as f:
    for y in range(150,1650,300):
        i = 0
        for x in range(150,1650,300):
            sum = 0
            for n in range(repetition):
                sinr = sc.compute_sinr(46,18,0,7,0,0.7,coor.Coordinate(x,y),coor.Coordinate(150,150),2,-104.5,6,363*10**-9,False,"URBAN_MACROCELL",25,1.5,20,20)
                sum += sinr
            sinr_medio = sum/repetition
            f.write("ue[{}]({},{}): {}\n".format(k,x,y, sinr_medio))
            sinrMap[j][i] = sinr_medio
            k += 1
            i += 1
        j += 1

