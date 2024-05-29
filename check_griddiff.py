"""
This function compares two hdf5 file grids - `foo` and `bar` - to one another.
"""
import argparse
import difflib
import json
import os

import h5py
import numpy as np


parser = argparse.ArgumentParser()
parser.add_argument(
    "-g",
    "--grids",
    nargs="+",
)


def main(foo: str, bar: str):
    assert os.path.exists(foo)
    assert os.path.exists(bar)
    assert foo.endswith(".hdf5")
    assert bar.endswith(".hdf5")

    print(f"COMPARING {foo} to {bar}")

    run_diff(
        h5py.File(foo),
        h5py.File(bar),
        foo,
        bar,
        {"solar_models": {"*": {}}, "header": {}},
    )


def run_diff(foo, bar, fooname: str, barname: str, subkeys, path=()):
    for k in commonify(foo, bar):
        if k in foo:
            if k in bar:
                print(".", *path, k, "- in both")
                if k in subkeys:
                    run_diff(foo[k], bar[k], fooname, barname, subkeys[k], (*path, k))
                elif "*" in subkeys:
                    run_diff(foo[k], bar[k], fooname, barname, subkeys["*"], (*path, k))
            else:
                print("X", *path, k, f" - only in {fooname}")
        else:
            print("Y", *path, k, f"- only in {barname}")


def commonify(foo, bar):
    "Produce the union of foo and bar in a sensible order."
    foolist = list(foo)
    barlist = list(bar)
    fooset = set(foolist)
    matcher = difflib.SequenceMatcher(a=foolist, b=barlist)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        barsublist = [k for k in barlist[j1:j2] if k not in fooset]
        for k in _commonify_merge(foolist[i1:i2], barsublist):
            yield k


def _commonify_merge(foo, bar):
    "Helper function used in commonify()."
    i = 0
    j = 0
    while i < len(foo) and j < len(bar):
        if foo[i] <= bar[j]:
            yield foo[i]
            i += 1
        else:
            yield bar[j]
            j += 1
    yield from foo[i:]
    yield from bar[j:]


if __name__ == "__main__":
    args = parser.parse_args()
    assert len(args.grids) == 2
    main(*args.grids)
