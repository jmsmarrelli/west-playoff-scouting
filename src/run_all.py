"""Rebuild the three studies from the pinned public source files."""

import os

os.environ.setdefault("OMP_NUM_THREADS", "4")
import argparse
from . import cohorts, foul_channel, shot_model, glass_pressure, data, figures, publish


def run(fetch=False):
    if fetch:
        data.fetch()
    for module in [cohorts, foul_channel, shot_model, glass_pressure]:
        module.run()
        print(module.__name__, "complete", flush=True)
    data.database()
    figures.run()
    publish.run()
    print("Tables, charts, SQL summaries and articles rebuilt", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true")
    run(parser.parse_args().fetch)
