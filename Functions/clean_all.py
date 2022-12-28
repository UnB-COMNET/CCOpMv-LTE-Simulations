from pathlib import Path
import os
import shutil
import general_functions as genf

def main():
    result_dir = "Solutions"
    project_dir = '../Network_CCOpMv'
    sim_dir = '_5G/simulations'
    move_config_name = 'ilp_move_users'
    chosen_seeds = [2,3,4,5,6,7,10,11,12,13]
    extra_dir = ['disaster_percentage','micro_power']
    disaster_percentage = 0
    micro_power = 30 #dBm
    kwargs = {'disaster_percentage': disaster_percentage, 'micro_power': micro_power}

    clean_all(chosen_seeds=chosen_seeds, result_dir=result_dir, project_dir=project_dir,
              sim_dir=sim_dir, move_config_name=move_config_name, extra_dir=extra_dir, **kwargs)

def clean_all(chosen_seeds: list[int], result_dir: str, project_dir: str, sim_dir: str,
              move_config_name: str, extra_dir: list[str], **kwargs):

    for chosen_seed in chosen_seeds:
        new_result_dir= result_dir
        new_sim_dir= sim_dir

        for param in extra_dir:
            new_result_dir = os.path.join(new_result_dir, (f'{param}_{kwargs[param]}' if param in kwargs else ''))
            new_sim_dir = os.path.join(new_sim_dir, (f'{param}_{kwargs[param]}' if param in kwargs else ''))
        
        sim_dir_full = os.path.join(project_dir, new_sim_dir, f'chosen_seed_{chosen_seed}')
        result_dir_full = os.path.join(new_result_dir, f'chosen_seed_{chosen_seed}')
        xml_filename = genf.gen_movement_filename(move_config_name, chosen_seed, snapshot= True)

        if os.path.isfile(xml_filename):
            os.remove(xml_filename)
        else:
            print(f'Cannot find file "{xml_filename}"')
        if os.path.isdir(result_dir_full):
            shutil.rmtree(result_dir_full)
            Path(result_dir_full).mkdir(parents=True)
        else:
            print(f'Cannot find dir "{result_dir_full}"')
        if os.path.isdir(sim_dir_full):
            shutil.rmtree(sim_dir_full)
            Path(sim_dir_full).mkdir(parents=True)
        else:
            print(f'Cannot find dir "{sim_dir_full}"')

if __name__ == "__main__":
    main()