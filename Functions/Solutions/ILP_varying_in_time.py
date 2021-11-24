from ortools.linear_solver import pywraplp
import random
import math 

def ccop_mv_MILP(
    Max_Space,
    Max_Time, 
    users_t_m, 
    MAX_USER_PER_ANTENNA_m, 
    antenasmap_m, 
    snr_map_mn, 
    MIN_SNR_m,
    MIN_TIME=2):
    
    M = Max_Space
    T = Max_Time
    delta = MIN_TIME
    

    solver = pywraplp.Solver("Mixed Integer Programming", pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

    ## Decision variables
    #Placement variables
    xtm = [[solver.NumVar(0, antenasmap_m[m], "$x_{%d,%d}$"%(t,m)) for m in range(0,M)] for t in range(0, T)]
    #Past of the placement variables
    past_xtm = [[solver.NumVar(0, solver.infinity(), "$past_x_{%d,%d}$"%(t,m)) for m in range(0,M)] for t in range(0, T)]
    #Connection variables
    ytmn = [[[solver.BoolVar("$y_{%d,%d,%d}$"%(t,m,n)) for n in range(0,M)] for m in range(0,M)] for t in range(0, T)]

    ## Constraints
    # Antennas must serve n areas only if the signal meet a minimum SNR omega
    for t in range(0,T):
        for m in range(0, M):
            for n in range(0,M):
                ct = solver.Constraint(-solver.infinity(), snr_map_mn[m][n])
                ct.SetCoefficient(ytmn[t][m][n], MIN_SNR_m[n])
    # Antenas m support a max number of users connected
    for t in range(0,T):
        for m in range(0,M):
            ct = solver.Constraint(-solver.infinity(), MAX_USER_PER_ANTENNA_m[m])
            for n in range(0,M):
                ct.SetCoefficient(ytmn[t][m][n], users_t_m[t][n])
    # A sector n will be only connected to a single antenna in sector m
    for t in range(0,T):
        for n in range(0,M):
            if (users_t_m[t][n] > 0):
                ct = solver.Constraint(1,1)
                for m in range(0,M):
                    ct.SetCoefficient(ytmn[t][m][n], 1)

    # Create near past variable
    for t in range(delta+1, T):
        for m in range(0,M):
            ct=solver.Constraint(0,0)
            ct.SetCoefficient(past_xtm[t][m], -1)
            for j in range(t-delta-1, t-1):
                ct.SetCoefficient(xtm[t][m], 1)

    # Determine the temporal relationship
    LARGE_NUM=delta+1
    for m in range(0,M):
        for t in range(delta+1, T):
            ct=solver.Constraint(delta-LARGE_NUM, solver.infinity())
            ct.SetCoefficient(xtm[t][m], LARGE_NUM) # We can always install a new antenna
            ct.SetCoefficient(xtm[t-1][m], -LARGE_NUM) # In case the near past is 0 the present can also be 0
            ct.SetCoefficient(past_xtm[t][m], 1) # In case the near past is 1, 


    # Connections to n are performed only if an antenna exists in m 
    for t in range(0, T):
        for m in range(0,M):
            for n in range(0,M):
                ct = solver.Constraint(-solver.infinity(),0)
                ct.SetCoefficient(ytmn[t][m][n], 1)
                ct.SetCoefficient(xtm[t][m], -1)

                # Constraint - if antenna in m then serve m
                if m == n:
                    ct = solver.Constraint(0,0)
                    ct.SetCoefficient(ytmn[t][m][n], 1)
                    ct.SetCoefficient(xtm[t][m], -1)
    objective = solver.Objective()
    for t in range(0, T):
        for m in range(0,M):
            objective.SetCoefficient(xtm[t][m], 1)
            objective.SetMinimization()

    status = solver.Solve()
    if status == pywraplp.Solver.OPTIMAL:
        print(objective.Value()/T)
        for t in range(0,T):
            print("t=%d"%t)
            for m in range(0,M):
                print(xtm[t][m],"=", xtm[t][m].solution_value())
                if xtm[t][m].solution_value() > 0:
                    users=0
                    snr_medio=0
                    contador=0
                    for n in range(0,M):
                        if ytmn[t][m][n].solution_value() > 0 :
                            contador+=1
                            snr_medio+=snr_map_mn[m][n]
                            print("\t",ytmn[t][m][n], "=",snr_map_mn[m][n],"dB")
                            users+=users_t_m[t][n]
                    print("\t\tSNR medio:", snr_medio/contador)
                    print("\t\tUsuarios totais:", users)





    else:
        print("Not feasible")
    

Max_Space=6
Max_Time=6
users_t_m = [[ math.ceil(random.random()*20) for m in range(0,Max_Space)] for t in range(0,Max_Time)]
antenasmap_m = [1,1,1,1,0,0]
MAX_USER_PER_ANTENNA_m=[60,40,60,40,60,40]
snr_map_mn=[[random.random()*50 for n in range(0,Max_Space)] for m in range(0,Max_Space)]
MIN_SNR_m=[20,30,10,25,20,15]


ccop_mv_MILP(Max_Space,
    Max_Time, 
    users_t_m, 
    MAX_USER_PER_ANTENNA_m, 
    antenasmap_m, 
    snr_map_mn, 
    MIN_SNR_m)
