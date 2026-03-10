from app.constants import SolutionType
from pathlib import Path
from app.run_all import DirectoryConfig
from app.run_all import RunConfig
from app.run_all import ScenarioConfig
from app.run_all import SimulationPipeline


def main():
    """Entry point: build default pipeline config and run."""
    pipeline = SimulationPipeline(
        chosen_seeds=[2],
        scenario_config=ScenarioConfig(
            size_x=4000,
            size_y=4000,
            size_sector=40,
            n_macros=1,
            min_sinrs=[5],
            modes=[
                SolutionType.ILP_SINGLE,
                SolutionType.GA,
            ],
        ),
        run_config=RunConfig(only_solver=True),
        directory_config=DirectoryConfig(
            project_dir=str(Path(__file__).parent.parent / "SimulationsCCOpMv"),
            sim_dir=str(
                Path(__file__).parent.parent / "SimulationsCCOpMv" / "simulations"
            ),
            csv_dir=str(Path(__file__).parent.parent / "SimulationsCCOpMv" / "results"),
            net_dir=str(
                Path(__file__).parent.parent / "SimulationsCCOpMv" / "networks"
            ),
            result_dir=str(
                Path(__file__).parent.parent / "SimulationsCCOpMv" / "solutions"
            ),
            extra_dir=["disaster_percentage", "micro_power", "chosen_seed"],
        ),
    )
    pipeline.run()


if __name__ == "__main__":
    main()
