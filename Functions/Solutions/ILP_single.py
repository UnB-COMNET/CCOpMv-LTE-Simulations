from ortools.linear_solver import pywraplp
from sinr_comput import linear_to_db
from _5G_Scenarios.ILP_configs import gen_solver_result_filename
import math 

def ccop_mv_MILP(
    Max_Space,#Total number of sectors
    #Max_Time,#Total number of slices of time
    #users_t_m,#Users positions in each slice of time
    users_m,#Users positions
    #(Utilizar o mesmo modelo que antes? Considerar "antenas" aleatorias ou fazer de acordo com o mapa)
    MAX_USER_PER_ANTENNA_m,#Max de usuarios da antena em m
    antenasmap_m,#Mapa binario de onde podem ter antenas
    snr_map_mn,#Matriz [local_antena][local_usuario] Watts
    MIN_SNR_m,#Minimo SNR dado pela antena de local m Watts
    distance_mn,
    MIN_DIS=2,
    FIRST_ANTENNA=1,
    result_dir = '.'):

    M = Max_Space

    solver = pywraplp.Solver("Mixed Integer Programming", pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

    ## Decision variables
    #Placement variables
    xm = [0 if antenasmap_m[m] < 1 else solver.BoolVar("$x_{%d}$"%(m)) for m in range(0,M)]
    #Connection variables
    ymn = [0 if antenasmap_m[m] == 0 else [solver.BoolVar("$y_{%d,%d}$"%(m,n)) for n in range(0,M)] for m in range(0,M)]

    ## Constraints
    #The first antenna must be in place at time 0
    if antenasmap_m[FIRST_ANTENNA] == 0:
        raise ValueError('FIRST ANTENNA CANNOT BE PLACED IN AN INVALID PLACE')
    ct=solver.Constraint(1, 1)
    ct.SetCoefficient(xm[FIRST_ANTENNA], 1)

    # An antenna must be connected to the backhaul
    for m in range(0,M):
        if antenasmap_m[m] != 0: 
            if m != FIRST_ANTENNA:
                ct=solver.Constraint(-solver.infinity(),0)
                ct.SetCoefficient(xm[m], 1)
                for n in range(0, M):
                    if antenasmap_m[n] != 0: 
                        if distance_mn[n][m] <= MIN_DIS:
                            if m != n:
                                ct.SetCoefficient(xm[n], -1)

    # Antennas must serve n areas only if the signal meet a minimum SNR omega
    for m in range(0, M):
        if antenasmap_m[m] != 0:
            for n in range(0,M):
                if users_m[n] > 0:
                    ct = solver.Constraint(-solver.infinity(), snr_map_mn[m][n])
                    ct.SetCoefficient(ymn[m][n], MIN_SNR_m[n])
                
    # Antenas m support a max number of users connected
    for m in range(0,M):
        if antenasmap_m[m] != 0:
            ct = solver.Constraint(-solver.infinity(), MAX_USER_PER_ANTENNA_m[m])
            for n in range(0,M):
                ct.SetCoefficient(ymn[m][n], users_m[n])
                
    # A sector n will be only connected to a single antenna in sector m
    for n in range(0,M):
        if users_m[n] > 0:
            ct = solver.Constraint(1,1)
            for m in range(0,M):
                if antenasmap_m[m] != 0:
                    ct.SetCoefficient(ymn[m][n], 1)

    # Connections to n are performed only if an antenna exists in m and if there are users in n
    for m in range(0,M):
        if antenasmap_m[m] != 0:
            for n in range(0,M):
                if users_m[n] > 0:
                    if m != n:
                        ct = solver.Constraint(-solver.infinity(),0)
                        ct.SetCoefficient(ymn[m][n], 1)
                        ct.SetCoefficient(xm[m], -1)
                    # Constraint - if antenna in m then serve m
                    else:
                        ct = solver.Constraint(0,0)
                        ct.SetCoefficient(ymn[m][n], 1)
                        ct.SetCoefficient(xm[m], -1)


    objective = solver.Objective()

    for m in range(0,M):
        if antenasmap_m[m] != 0:
            objective.SetCoefficient(xm[m], 1)
    objective.SetMinimization()

    status = solver.Solve()
    if status == pywraplp.Solver.OPTIMAL:
        with open(gen_solver_result_filename(result_dir, 'single', int(linear_to_db(MIN_SNR_m[0]))), 'w') as f:
            print("\nMédia de carros:", objective.Value())
            found=[]
            for m in range(0,M):
                if antenasmap_m[m] != 0:
                    if xm[m].solution_value() > 0.9:
                        found.append(m)
                        print(xm[m])
                        users=0
                        snr_medio=0
                        contador=0
                        for n in range(0,M):
                            if ymn[m][n].solution_value() > 0.9 :
                                contador+=1
                                snr_medio+=snr_map_mn[m][n]
                                print("\t",ymn[m][n], "=",10*math.log10(snr_map_mn[m][n]),"dB")
                                users+=users_m[n]
                                f.write("0 {m} {n}\n".format(m= m, n= n))
                        if contador > 0 :
                            print("\t\tSNR medio:", 10*math.log10(snr_medio/contador))
                        print("\t\tUsuarios totais:", users)
            print("Distances:")
            for i in found:
                for j in found:
                    if i < j :
                        print(f"{i} : {j} = {distance_mn[i][j]}")
            f.write("--- Done ---\n")
    else:
        print("Not feasible")
