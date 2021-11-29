from math import log, log10
import numpy as np
import random
from coordinates import Coordinate

#speed m/s
def compute_sinr(tx_power:float, tx_gain: float, rx_gain: float, noise_figure: float, speed: float,
                 carrier_frequency: float, ue_coord: Coordinate, tx_coord: Coordinate,
                 cable_loss: float = 2, thermal_noise: float = -104.5, #n_bands: int = 6,
                 fading_paths: int = 6, delay_rms: float = 363*10**-9, los: bool = False,
                 scenario: str = "URBAN_MACROCELL", h_enbs: float = 25, h_ues: float = 1.5,
                 h_building: float = 20, w_street: float = 20):

  fading = jakes_fadding(fading_paths, speed, delay_rms, carrier_frequency, sim_time= 0.001)

  attenuation = compute_attenuation(ue_coord, tx_coord, speed, los, scenario, h_enbs, h_ues,
                                    carrier_frequency, h_building, w_street,True)

  recv_power = tx_power
  recv_power += tx_gain + rx_gain - cable_loss - attenuation

  final_recv_power = recv_power + fading

  den = dbm_to_linear(thermal_noise + noise_figure)

  snr = final_recv_power - linear_to_dbm(den)

  return db_to_linear(snr)

def jakes_fadding(fading_paths: int, speed: float, delay_rms: float, carrier_frequency: float,
                  sim_time: float = 0.001):
  #jakes_map = None

  speed_of_light = 299792458.0

  #convert carrier frequency from GHz to Hz
  f = carrier_frequency * 1000000000

  t = sim_time - 0.001

  angle_arrival = []
  delay_spread = []

  re_h = 0
  im_h = 0

  doppler_shift = (speed * f) / speed_of_light

  for i in range(fading_paths):
    
    # get angle of arrivals
    angle_arrival.append(np.cos(random.random()*np.pi))

    #get delay spread
    delay_spread.append(random.expovariate(1/delay_rms))

    phi_d = angle_arrival[i]*doppler_shift

    phi_i = delay_spread[i] * f

    phi = 2 * np.pi * (phi_d * t - phi_i)

    attenuation = 1.0/np.sqrt(fading_paths)

    re_h += attenuation * np.cos(phi)
    im_h -= attenuation * np.sin(phi)

  result = linear_to_db(re_h * re_h + im_h * im_h)
  #this may be >1 due to constructive interference
  if (result <= 1):
    #print("ERROR: invalid result computing jakes fading")
    return 0

  return result


# PATHLOSS + SHADOWING
def compute_attenuation(ue_coord: Coordinate, tx_coord: Coordinate, speed: int, los: bool,
                        scenario: str, h_enbs: float, h_ues: float, carrier_frequency: float,
                        h_building: float, w_street: float, tolerateMaxDistViolation: bool = False):

  distance = np.sqrt((ue_coord.x - tx_coord.x)**2 + (ue_coord.y - tx_coord.y)**2 + (ue_coord.z - tx_coord.z)**2)
  
  attenuation = compute_path_loss(distance, los, scenario, h_enbs, h_ues, carrier_frequency, h_building, w_street,tolerateMaxDistViolation)

  attenuation += compute_shadowing(distance, speed, los, scenario)

  return attenuation

def compute_path_loss(distance: float, los: bool, scenario: str, h_enbs: float, h_ues: float,
                      carrier_frequency: float, h_building: float, w_street: float, tolerateMaxDistViolation: bool = False):
  
  if scenario == "URBAN_MACROCELL":
    path_loss = compute_urban_macro(distance, los, carrier_frequency, h_enbs, h_ues, h_building, w_street,tolerateMaxDistViolation)

  else:
    print("ERROR computing pathloss: invalid scenario")
    path_loss = 1000

  return path_loss
def compute_urban_macro(distance: float, los: bool, carrier_frequency: float, h_enbs: float = 25,
                        h_ues: float = 1.5, h_building: float = 20, w_street: float = 20, tolerateMaxDistViolation: bool = False):

  speed_of_light = 299792458.0

  if distance < 10:
    distance = 10

  dbp = 4 * (h_enbs - 1) * (h_ues - 1) * ((carrier_frequency * 1000000000) / speed_of_light)

  #Considering tolerateMaxDistViolation = true in the simulation
  if distance >= 5000:
        if tolerateMaxDistViolation:
          return 1000
        else:
          print("ERROR: Urban Macrocell Model is valid for distance < 5000m")
          return

  else:
    #LOS
    if los:
      if distance < dbp: 
        return 22 * log10(distance) + 28 + 20 * log10(carrier_frequency)

      else: 
        att = 40 * log10(distance) + 7.8 - 18 * log10(h_enbs - 1) \
             -18 * log10(h_ues - 1) + 2 * log10(carrier_frequency)

        return att

    #NLOS
    else:      
      att = 161.04 - 7.1 * log10(w_street) + 7.5 * log10(h_building) - (24.37 - 3.7 * pow(h_building/h_enbs, 2))\
          * log10(h_enbs) + (43.42 - 3.1 * log10(h_enbs)) * (log10(distance) - 3) + 20 * log10(carrier_frequency)\
          - (3.2 * (pow(log10(11.75 * h_ues), 2)) - 4.97)

      return att

def compute_shadowing(distance: float, speed: float, los: bool, scenario: str):

  std_dev = 0

  if scenario == "URBAN_MACROCELL":
    if los: std_dev = 4
    else: std_dev = 6

  #Get the log normal shadowing with std deviation stdDev
  att = random.normalvariate(0, std_dev)

  #Not computing case considering ue moviment
  return att

def linear_to_db(linear: float):
  return 10 * np.log10(linear)

def linear_to_dbm(linear: float):
  return 10 * log10(1000 * linear)

def dbm_to_linear(db: float):
  return pow(10, (db - 30) / 10)

def db_to_linear(db: float):
  return pow(10, db/10)