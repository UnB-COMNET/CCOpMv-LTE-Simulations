import numpy as np
import typing as ty
import random
from Functions.geometry import Coordinate
import geometry as geo

#speed m/s
def compute_sinr(tx_gain: float, rx_gain: float, noise_figure: float, speed: float,
                 carrier_frequency: float, seed: int,
                 cable_loss: float = 2, thermal_noise: float = -104.5, #n_bands: int = 6,
                 fading_paths: int = 6, delay_rms: float = 363**-9, los: bool = False,
                 scenario: str = "URBAN_MACROCELL"):

  fading = jakes_fadding(fading_paths, speed, delay_rms, carrier_frequency, seed)

  attenuation = compute_attenuation()

  recv_power = tx_gain + rx_gain - cable_loss - attenuation

  final_recv_power = recv_power + fading

  den = thermal_noise + noise_figure

  snr = final_recv_power - den

  return snr

def jakes_fadding(fading_paths: int, speed: float, delay_rms: float, carrier_frequency: float, seed: int, sim_time: float = 0.001):
  #jakes_map = None
 
  random.seed(seed)

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
    print("ERROR: invalid result computing jakes fading")
    return 0

  return result


# PATHLOSS + SHADOWING
def compute_attenuation(ue_coord: Coordinate, tx_coord: Coordinate, speed: int, los: bool,
                        scenario: str):
  pass
  #distance = np.sqrt((ue_coord.x - tx_coord.x)**2 + (ue_coord.y - tx_coord.y)**2 + (ue_coord.z - tx_coord.z)**2)

  #attenuation = compute_path_loss(distance, los)
  #print(attenuation)

  #attenuation += compute_shadowing(distance, speed)

#def compute_path_loss(distance: float, los: bool, scenario: str):
#  if scenario == "URBAN_MACROCELL":
#    compute_urban_macro(distance, los)
#  else:
#    print("ERROR computing pathloss: invalid scenario")
#    return 0

#def compute_urban_macro(distance: float, los: bool):
#  if distance < 10:
#    distance = 10

  


def linear_to_db(linear: float):
  return 10 * np.log10(linear)

#def db_to_linear(db: float):
#  return 10**(db/10)