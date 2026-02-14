from ortools.linear_solver import pywraplp
from app.core.sinr_comput import linear_to_db
from app.helpers.general_functions import gen_solver_result_filename
import math 

def ccop_mv_MILP(
    Max_Space,
    Max_Time, 
    users_t_m, 
    MAX_USER_PER_ANTENNA_m, 
    antenasmap_m, 
    snr_map_mn, 
    MIN_SNR_m,
    distance_mn,
    MIN_TIME=2,
    MIN_DIS=2,
    FIRST_ANTENNA=1,
    result_dir = '.'):
    
    M = Max_Space
    T = Max_Time

    solver = pywraplp.Solver("Mixed Integer Programming", pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

    ## Decision variables

    # Antennas must provide connection or they will be subused

    #Placement variables
    xtm = [[0 if antenasmap_m[m] < 1 else solver.BoolVar("$x_{%d,%d}$"%(t,m)) for m in range(0,M)] for t in range(0, T)]
    #Past of the placement variables
    past_xtm = [[0 if t < MIN_TIME or m == FIRST_ANTENNA or antenasmap_m[m] < 1 else solver.NumVar(0, solver.infinity(), "$pastx_{%d,%d}$"%(t,m)) for m in range(0,M)] for t in range(0, T)]
    #Connection variables
    ytmn = [[0 if antenasmap_m[m] == 0 else [solver.BoolVar("$y_{%d,%d,%d}$"%(t,m,n)) for n in range(0,M)] for m in range(0,M)] for t in range(0, T)]

    ## Constraints
    #The first antenna must be in place at time 0
    if antenasmap_m[FIRST_ANTENNA] == 0:
        raise ValueError('FIRST ANTENNA CANNOT BE PLACED IN AN INVALID PLACE')
    for t in range(0, T):
        ct=solver.Constraint(1, 1)
        ct.SetCoefficient(xtm[t][FIRST_ANTENNA], 1)

    # An antenna must be connected to the backhaul
    for t in range(0,T):
        for m in range(0,M):
            if antenasmap_m[m] != 0: 
                if m != FIRST_ANTENNA:
                    ct=solver.Constraint(-solver.infinity(),0)
                    ct.SetCoefficient(xtm[t][m], 1)
                    for n in range(0, M):
                        if antenasmap_m[n] != 0: 
                            if distance_mn[n][m] <= MIN_DIS:
                                if m != n:
                                    ct.SetCoefficient(xtm[t][n], -1)

    # Antennas must serve n areas only if the signal meet a minimum SNR omega
    for t in range(0,T):
        for m in range(0, M):
            if antenasmap_m[m] != 0:
                for n in range(0,M):
                    if users_t_m[t][n] > 0:
                        ct = solver.Constraint(-solver.infinity(), snr_map_mn[m][n])
                        ct.SetCoefficient(ytmn[t][m][n], MIN_SNR_m[n])                

    # Antenas m support a max number of users connected
    for t in range(0,T):
        for m in range(0,M):
            if antenasmap_m[m] != 0:
                ct = solver.Constraint(-solver.infinity(), MAX_USER_PER_ANTENNA_m[m])
                for n in range(0,M):
                    ct.SetCoefficient(ytmn[t][m][n], users_t_m[t][n])

    # A sector n will be only connected to a single antenna in sector m
    for t in range(0,T):
        for n in range(0,M):
            if users_t_m[t][n] > 0:
                ct = solver.Constraint(1,1)
                for m in range(0,M):
                    if antenasmap_m[m] != 0:
                        ct.SetCoefficient(ytmn[t][m][n], 1)

    # Create near past variable
    for t in range(MIN_TIME, T):
        for m in range(0,M):
            if antenasmap_m[m] != 0: 
                if m != FIRST_ANTENNA:
                    ct=solver.Constraint(0,0)
                    ct.SetCoefficient(past_xtm[t][m], -1)
                    for j in range(t-MIN_TIME, t):
                        ct.SetCoefficient(xtm[j][m], 1)

    # Determine the temporal relationship
    for m in range(0,M):
        if antenasmap_m[m] != 0:
            if m != FIRST_ANTENNA:
                for t in range(1, T):
                    if t < MIN_TIME:
                        ct=solver.Constraint(-1, 0)
                        ct.SetCoefficient(xtm[t][m], -1) 
                        ct.SetCoefficient(xtm[t-1][m], 1) # In case the near past is 0 the present can also be 0
                    else:
                        ct=solver.Constraint(0, solver.infinity())
                        ct.SetCoefficient(xtm[t][m], MIN_TIME) # We can always install a new antenna
                        ct.SetCoefficient(xtm[t-1][m], -MIN_TIME) # In case the near past is 0 the present can also be 0
                        ct.SetCoefficient(past_xtm[t][m], 1) # In case the near past is 1, 

    # Connections to n are performed only if an antenna exists in m and if there are users in n
    for t in range(0, T):
        for m in range(0,M):
            if antenasmap_m[m] != 0:
                for n in range(0,M):
                    if users_t_m[t][n] > 0:
                        if m != n:
                            ct = solver.Constraint(-solver.infinity(),0)
                        # Constraint - if antenna in m then serve m
                        else:
                            ct = solver.Constraint(0,0)
                        ct.SetCoefficient(ytmn[t][m][n], 1)
                        ct.SetCoefficient(xtm[t][m], -1)


    objective = solver.Objective()
    for t in range(0, T):
        for m in range(0,M):
            if antenasmap_m[m] != 0:
                objective.SetCoefficient(xtm[t][m], 1)
    objective.SetMinimization()

    status = solver.Solve()
    if status == pywraplp.Solver.OPTIMAL:
        with open(gen_solver_result_filename(result_dir, 'varying', math.ceil(linear_to_db(MIN_SNR_m[0]))), 'w') as f:
            print("\nMédia de carros:", objective.Value()/T)
            for t in range(0,T):
                print("t=%d"%t)
                found=[]
                for m in range(0,M):
                    if antenasmap_m[m] != 0:
                        if xtm[t][m].solution_value() > 0.9:
                            found.append(m)
                            print(xtm[t][m])
                            if t >= MIN_TIME and m != FIRST_ANTENNA:
                                    print("\t",past_xtm[t][m], ":",past_xtm[t][m].solution_value())
                            users=0
                            snr_medio=0
                            contador=0
                            for n in range(0,M):
                                if ytmn[t][m][n].solution_value() > 0.9 :
                                    contador+=1
                                    snr_medio+=snr_map_mn[m][n]
                                    print("\t",ytmn[t][m][n], "=",10*math.log10(snr_map_mn[m][n]),"dB")
                                    users+=users_t_m[t][n]
                                    f.write("{t} {m} {n}\n".format(t= t, m= m, n= n))
                            if contador > 0 :
                                print("\t\tSNR medio:", 10*math.log10(snr_medio/contador))
                            print("\t\tUsuarios totais:", users)
                            if users == 0:
                                f.write("{t} {m} {n}\n".format(t= t, m= m, n= -1))
                print("Distances:")
                for i in found:
                    for j in found:
                        if i < j :
                            print(f"{i} : {j} = {distance_mn[i][j]}")
            f.write("--- Done ---\n")
    else:
        print("Not feasible")