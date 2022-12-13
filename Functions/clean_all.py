from pathlib import Path
import os
import shutil

def main():
    result_dir = "Solutions"
    project_dir = '../Network_CCOpMv'
    sim_dir = '_5G/simulations'

    clean_all(result_dir=result_dir, project_dir=project_dir, sim_dir=sim_dir)

def clean_all(result_dir: str, project_dir: str, sim_dir: str):

    sim_path = os.path.join(project_dir, sim_dir)

    shutil.rmtree(result_dir)
    Path(result_dir).mkdir(parents=True)
    shutil.rmtree(sim_path)
    Path(sim_path).mkdir(parents=True)

if __name__ == "__main__":
    main()