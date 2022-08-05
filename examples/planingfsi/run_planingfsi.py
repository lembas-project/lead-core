import dataclasses
import shutil
import subprocess
from pathlib import Path

import numpy
import pandas
from matplotlib import pyplot
from planingfsi.dictionary import load_dict_from_file

MIN_FROUDE_NUM = 0.2
MAX_FROUDE_NUM = 3.0

FLAT_PLATE_ROOT = Path(__file__).parent / "flat_plate"


@dataclasses.dataclass
class PlaningPlateResults:
    drag: float
    lift: float
    moment: float


def run_planingfsi(froude_num: float, angle_of_attack: float) -> PlaningPlateResults:
    if not (MIN_FROUDE_NUM <= froude_num <= MAX_FROUDE_NUM):
        raise ValueError("Input Froude number must be in the range 0.2 <= Fr <= 3.0")

    case_dir_base = FLAT_PLATE_ROOT / "flat_plate_base"

    case_dir = FLAT_PLATE_ROOT / f"Fr={froude_num:0.1f}_AOA={angle_of_attack:0.1f}"
    if not case_dir.exists():
        shutil.copytree(case_dir_base, case_dir)

        with (case_dir / "configDict").open("w") as fp:
            fp.write("baseDict: './configDict.base'\n")
            fp.write(f"Fr: {froude_num}\n")
            fp.write(f"AOA: {angle_of_attack}\n")

        subprocess.run(["planingfsi", "mesh"], cwd=str(case_dir))
        subprocess.run(["planingfsi", "run"], cwd=str(case_dir))

    # Find the latest time directory to load results from
    results_dir = sorted(
        case_dir.glob("[0-9]*"), key=lambda d: int(d.name), reverse=True
    )[0]
    results_dict = load_dict_from_file(results_dir / "forces_total.txt")

    return PlaningPlateResults(
        drag=results_dict["Drag"],
        lift=results_dict["Lift"],
        moment=results_dict["Moment"],
    )


if __name__ == "__main__":
    froude_nums = numpy.linspace(0.5, 3.0, 7)
    AOA_nums = numpy.linspace(5.0, 15.0, 5)

    all_results = []

    for froude_num in froude_nums:
        for aoa in AOA_nums:
            results = run_planingfsi(froude_num, aoa)
            results_dict = dataclasses.asdict(results)
            results_dict.update({"froude_num": froude_num, "aoa": aoa})
            all_results.append(results_dict)

    df = pandas.DataFrame.from_records(all_results)

    df.plot.scatter(x="froude_num", y="lift", c="aoa")

    pyplot.show()
