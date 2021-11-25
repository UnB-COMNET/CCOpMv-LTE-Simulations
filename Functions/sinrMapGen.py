from math import ceil, sin
import sinr_comput as sc
import coordinates as coor

file_name = "sinrMap.txt"

repetition = 10
num_sector = 4
d_height = 4000
d_width = d_height
d_region = 2000
positions = range(ceil(d_region/2), ceil(d_width + d_region/2), d_region)
k = 0 
j = 0
with open(file_name, 'w') as f:
    f.write("[")
    for yenb in positions:
        for xenb in positions:
            f.write("[")
            k = 0
            for y in positions:
                i = 0
                for x in positions:
                    sum = 0
                    for n in range(repetition):
                        sinr = sc.compute_sinr(46,18,0,7,0,0.7,coor.Coordinate(x,y),coor.Coordinate(xenb,yenb),2,-104.5,6,363*10**-9,False,"URBAN_MACROCELL",25,1.5,20,20)
                        sum += sinr
                    sinr_medio = sum/repetition
                    f.write("{}".format(sinr_medio))
                    if k != num_sector-1:
                        f.write(",")                    
                    k += 1
            
            f.write("]")
            if not(yenb == 750 and xenb == 750) :        
                f.write(",")

    f.write("]")

