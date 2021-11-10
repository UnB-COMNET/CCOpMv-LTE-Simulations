import numpy as np
import typing as ty
from random import random
import geometry as geo

def compute_sinr(tx_gain: float, rx_gain: float, noise_figure: float,
                 cable_loss: float = 2, thermal_noise: float = -104.5):

  fading = jakes_fadding()

  attenuation = get_attenuation()

  recv_power = tx_gain + rx_gain - cable_loss - attenuation

  final_recv_power = recv_power + fading

  den = thermal_noise + noise_figure

  snr = final_recv_power - den

  return snr

def jakes_fadding():
  pass

# PATHLOSS + SHADOWING
def get_attenuation():
  pass

def linear_to_db(linear: float):
  return 10 * np.log10(linear)