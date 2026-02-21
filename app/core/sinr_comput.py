from dataclasses import field
from dataclasses import dataclass
from math import log10
import numpy as np
import random
from app.core.coordinates import Coordinate

    
@dataclass(frozen=True, slots=True, kw_only=True)
class MapScenarioConfig:
    scenario: str = field(default="URBAN_MACROCELL")
    h_enbs: float = field(default=25)
    h_ues: float = field(default=1.5)
    h_building: float = field(default=20)
    w_street: float = field(default=20)
    los: bool = field(default=False)
    carrier_frequency: float = field(default=0.7)
    fading_paths: int = field(default=6)
    delay_rms: float = field(default=363 * 10**-9)
    thermal_noise: float = field(default=-104.5)
    cable_loss: float = field(default=2)
    gain_enb: float = field(default=18)
    gain_ue: float = field(default=0)
    ue_noise_figure: float = field(default=7)
    enb_noise_figure: float = field(default=5)
    enb_tx_power: float = field(default=46)
    ue_tx_power: float = field(default=26)

def compute_sinr(speed: float, ue_coord: Coordinate, tx_coord: Coordinate, scenario_config: MapScenarioConfig):
  """
    Computes the Signal-to-Interference-plus-Noise Ratio (SINR) for a LTE communication link according to the model implementation in the Simu5G simulator (and 3GPP).
    
    Note: This version does not compute interference.
  """
  fading = jakes_fadding(
    fading_paths=scenario_config.fading_paths, speed=speed, delay_rms=scenario_config.delay_rms, carrier_frequency=scenario_config.carrier_frequency, sim_time= 0.001
  )

  attenuation = compute_attenuation(
    ue_coord=ue_coord,
    tx_coord=tx_coord,
    speed=speed,
    los=scenario_config.los,
    scenario=scenario_config.scenario,
    h_enbs=scenario_config.h_enbs,
    h_ues=scenario_config.h_enbs,
    carrier_frequency=scenario_config.carrier_frequency,
    h_building=scenario_config.h_building,
    w_street=scenario_config.w_street,
    tolerateMaxDistViolation=True,
  )

  recv_power = scenario_config.enb_tx_power
  recv_power += scenario_config.gain_enb + scenario_config.gain_ue - scenario_config.cable_loss - attenuation

  final_recv_power = recv_power + fading

  den = dbm_to_linear(scenario_config.thermal_noise + scenario_config.ue_noise_figure)

  snr = final_recv_power - linear_to_dbm(den)

  return db_to_linear(snr)

def jakes_fadding(fading_paths: int, speed: float, delay_rms: float, carrier_frequency: float,
                  sim_time: float = 0.001):
  """
    Simulates Jakes fading (approximate) model for a wireless channel according to the model implementation in the Simu5G simulator.

    Args:
        fading_paths (int): Number of fading paths.
        speed (float): Speed of the mobile user (m/s).
        delay_rms (float): Root mean square (RMS) delay spread (s).
        carrier_frequency (float): Carrier frequency in GHz.
        sim_time (float, optional): Simulation time in seconds (default is 0.001).

    Returns:
        float: Resulting signal power level in dB.

    Note:
        The function simulates the Jakes fading model, a mathematical model
        used to describe the effect of multipath propagation in wireless channels.
  """
  speed_of_light = 299792458.0            # speed of light (m/s)

  #convert carrier frequency from GHz to Hz
  f = carrier_frequency * 1000000000      # frequency (Hz)

  t = sim_time - 0.001                    # time (s)

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


def compute_attenuation(ue_coord: Coordinate, tx_coord: Coordinate, speed: int, los: bool,
                        scenario: str, h_enbs: float, h_ues: float, carrier_frequency: float,
                        h_building: float, w_street: float, tolerateMaxDistViolation: bool = False):
  """
    Computes the total attenuation for a 3GPP LTE communication link according to the implementation in the Simu5G simulator.

    Args:
        ue_coord (Coordinate): Coordinates of the user equipment.
        tx_coord (Coordinate): Coordinates of the eNB.
        speed (int): Speed of the mobile user in m/s.
        los (bool): Line-of-sight flag.
        scenario (str): Wireless scenario in 3GPP. This version supports URBAN MACROCELL or URBAN MICROCELL.
        h_enbs (float): Height of eNBs in meters.
        h_ues (float): Height of user equipment in meters.
        carrier_frequency (float): Carrier frequency in GHz.
        h_building (float): Height of buildings in meters.
        w_street (float): Width of streets in meters.
        tolerateMaxDistViolation (bool, optional): Flag to consider maximum distance for model validity (default is False).

    Returns:
        float: Total attenuation which is the contribution of shadowing and path loss.
  """
  distance = np.sqrt((ue_coord.x - tx_coord.x)**2 + (ue_coord.y - tx_coord.y)**2 + (ue_coord.z - tx_coord.z)**2)    # Euclidian distance
  
  attenuation = compute_path_loss(distance, los, scenario, h_enbs, h_ues, carrier_frequency, h_building, w_street,tolerateMaxDistViolation)

  attenuation += compute_shadowing(distance, speed, los, scenario)

  return attenuation

def compute_path_loss(distance: float, los: bool, scenario: str, h_enbs: float, h_ues: float,
                      carrier_frequency: float, h_building: float, w_street: float, tolerateMaxDistViolation: bool = False):
  """
    Computes the path loss for a LTE communication link based on the specified 3GPP scenario.

    Args:
        distance (float): Distance between transmitter and receiver in meters.
        los (bool): Line-of-sight flag.
        scenario (str): Wireless scenario in 3GPP. This version supports URBAN MACROCELL or URBAN MICROCELL.
        h_enbs (float): Height of eNBs in meters.
        h_ues (float): Height of user equipment in meters.
        carrier_frequency (float): Carrier frequency in GHz.
        h_building (float): Height of buildings in meters.
        w_street (float): Width of streets in meters.
        tolerateMaxDistViolation (bool, optional): Flag to consider maximum distance for model validity (default is False).

    Returns:
        float: Path loss in dB.
  """
  if scenario == "URBAN_MACROCELL":
    path_loss = compute_urban_macro(distance, los, carrier_frequency, h_enbs, h_ues, h_building, w_street,tolerateMaxDistViolation)
  elif scenario == "URBAN_MICROCELL":
    path_loss = compute_urban_micro(distance, los, carrier_frequency, h_enbs, h_ues, tolerateMaxDistViolation)
  else:
    print("ERROR computing pathloss: invalid scenario")
    path_loss = 1000

  return path_loss

def compute_urban_macro(distance: float, los: bool, carrier_frequency: float, h_enbs: float = 25,
                        h_ues: float = 1.5, h_building: float = 20, w_street: float = 20, tolerateMaxDistViolation: bool = False):
  """
    Computes the path loss for an urban macrocell scenario 3GPP.

    Args:
        distance (float): Distance between transmitter and receiver in meters.
        los (bool): Line-of-sight flag.
        carrier_frequency (float): Carrier frequency in GHz.
        h_enbs (float, optional): Height of eNBs in meters (default is 25).
        h_ues (float, optional): Height of user equipment in meters (default is 1.5).
        h_building (float, optional): Height of buildings in meters (default is 20).
        w_street (float, optional): Width of streets in meters (default is 20).
        tolerateMaxDistViolation (bool, optional): Flag to consider maximum distance for model validity (default is False).

    Returns:
        float: Path loss in dB.
  """
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

def compute_urban_micro(distance: float, los: bool, carrier_frequency: float, h_enbs: float = 25,
                        h_ues: float = 1.5, tolerateMaxDistViolation: bool = False):
  """
    Computes the path loss for an urban microcell scenario 3GPP.

    Args:
        distance (float): Distance between transmitter and receiver in meters.
        los (bool): Line-of-sight flag.
        carrier_frequency (float): Carrier frequency in GHz.
        h_enbs (float, optional): Height of eNBs in meters (default is 25).
        h_ues (float, optional): Height of user equipment in meters (default is 1.5).
        tolerateMaxDistViolation (bool, optional): Flag to consider maximum distance for model validity (default is False).

    Returns:
        float: Path loss in dB.
  """
  speed_of_light = 299792458.0

  if distance < 10:
    distance = 10
  
  dbp = 4 * (h_enbs - 1) * (h_ues - 1) * ((carrier_frequency * 1000000000)/speed_of_light)

  if distance >= 5000:
    if tolerateMaxDistViolation:
      return 1000
    else:
      print("ERROR: Urban Microcell Model is valid for distance < 5000m")
      return
  else:
    # Line of sight
    if los:
      if distance < dbp:
        att = 22 * log10(distance) + 28 + 20 * log10(carrier_frequency)
      else:
        att = 40 * log10(distance) + 7.8 - 18 * log10(h_enbs - 1) \
              -18 * log10(h_ues - 1) + 2 * log10(carrier_frequency)

    # Non line of sight
    else:
      # [!!!] It changes compared to the macro scenario.
      att = 36.7 * log10(distance) + 22.7 + 26 * log10(carrier_frequency)
    
    return att

def compute_shadowing(distance: float, speed: float, los: bool, scenario: str):
  """
    Computes log-normal shadowing for a wireless communication link.

    Args:
        distance (float): Distance between transmitter and receiver in meters.
        speed (float): Speed of the mobile station in m/s.
        los (bool): Line-of-sight flag.
        scenario (str): Wireless scenario ("URBAN_MACROCELL" or "URBAN_MICROCELL").

    Returns:
        float: Log-normal shadowing in dB.
  """
  std_dev = 0

  if scenario == "URBAN_MACROCELL":
    if los: std_dev = 4
    else: std_dev = 6
  elif scenario == "URBAN_MICROCELL":
    if los: std_dev = 3
    else: std_dev = 4

  #Get the log normal shadowing with std deviation
  att = random.normalvariate(0, std_dev)

  return att

def linear_to_db(linear: float) -> float:
  """
  Converts a linear value to decibels (dB).

  Args:
      linear (float): Linear value.

  Returns:
      float: Value in decibels (dB).
  """
  return 10 * np.log10(linear)


def linear_to_dbm(linear: float) -> float:
    """
    Converts a linear value to decibels-milliwatts (dBm).

    Args:
        linear (float): Linear value.

    Returns:
        float: Value in decibels-milliwatts (dBm).
    """
    return 10 * log10(1000 * linear)


def dbm_to_linear(db: float) -> float:
    """
    Converts a decibels-milliwatts (dBm) value to linear.

    Args:
        db (float): Value in decibels-milliwatts (dBm).

    Returns:
        float: Linear value.
    """
    return pow(10, (db - 30) / 10)


def db_to_linear(db: float) -> float:
    """
    Converts a decibels (dB) value to linear.

    Args:
        db (float): Value in decibels (dB).

    Returns:
        float: Linear value.
    """
    return pow(10, db / 10)
