from pathlib import Path

def get_frameworks_path():
    user = 'juliano'
    if user == 'juliano':
        return r'../../../OmNET2'
    else:
        return r'../..'

def gen_file_name(mode: str, min_sinr: int):
    return f'ilp_{mode}_sliced_{str(min_sinr)}'

#Result_dir must have a 'logs' subdir
def gen_log_file_name(result_dir: str, file_name: str):
    log_dir = f"{result_dir}/logs"
    Path(log_dir).mkdir(parents=False, exist_ok=True)
    return f"{log_dir}/{file_name}.log"

def gen_sliced_config_pattern(min_sinr: int, mode: str, multi_carriers: bool, extra_config_name: str):
  return 'ilp_{}_sliced_{}'.format(mode, min_sinr) + ('_carriers' if multi_carriers else '') + ('_' + extra_config_name if extra_config_name != '' else '')

def gen_solver_result_filename(result_dir: str, mode: str, min_sinr: int):
  return result_dir + f"/result_{mode}_"+ str(min_sinr)+".txt"

def gen_movement_filename(config_name: str, seed: int, snapshot: bool= True):
  if snapshot:
    return config_name + f'-{seed}.sna'
  else:
    return config_name + f'-{seed}.ini'