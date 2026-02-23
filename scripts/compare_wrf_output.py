#!/usr/bin/env python
"""compare_wrf_output.py — Field-by-field comparison of two WRF intermediate output directories.

Use this script to verify that the refactored pgw4era package produces
bit-identical results to the original write_intermediate_ERA5_CMIP6anom.py
script (or any two runs over the same input data).

Usage
-----
    python scripts/compare_wrf_output.py --ref /path/to/old --new /path/to/new
    python scripts/compare_wrf_output.py --ref /old --new /new --atol 1e-5

The script reads every ERA5:YYYY-MM-DD_HH file found in both directories,
compares each field slab, and prints a summary.  Exit code 0 means all
compared files/fields are identical within the requested tolerance.
"""

from __future__ import annotations

import argparse
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# WRF intermediate binary reader
# ---------------------------------------------------------------------------


@dataclass
class WRFField:
    """One 2-D slab from a WRF intermediate file."""

    hdate: str
    field_name: str
    units: str
    desc: str
    xlvl: float
    nlons: int
    nlats: int
    slab: np.ndarray  # shape (nlons, nlats), big-endian float32

    @property
    def key(self) -> tuple[str, float]:
        """Unique identifier within a file: (field_name, pressure_level)."""
        return (self.field_name, float(self.xlvl))


def _read_fortran_record(f) -> bytes | None:
    """Read one big-endian Fortran unformatted record.

    Returns the raw record bytes, or None at EOF.
    """
    hdr = f.read(4)
    if len(hdr) < 4:
        return None
    (size,) = struct.unpack(">i", hdr)
    data = f.read(size)
    f.read(4)  # trailing length marker
    return data


def read_wrf_intermediate(path: Path) -> list[WRFField]:
    """Read all field slabs from a WRF intermediate (big-endian Fortran) file."""
    fields: list[WRFField] = []
    with open(path, "rb") as f:
        while True:
            # --- Record 1: format version (integer) ---
            rec = _read_fortran_record(f)
            if rec is None:
                break  # EOF

            # --- Record 2: field header ---
            rec = _read_fortran_record(f)
            # hdate(24) xfcst(f) map_source(32) field(9) units(25) desc(46)
            # xlvl(f) nlons(i) nlats(i) iproj(i)
            (hdate, _xfcst, _map_source, field_name, units, desc, xlvl, nlons, nlats, _iproj) = (
                struct.unpack(">24sf32s9s25s46sfiii", rec)
            )

            # --- Record 3: grid descriptor (ignored for comparison) ---
            _read_fortran_record(f)

            # --- Record 4: wind rotation flag (ignored for comparison) ---
            _read_fortran_record(f)

            # --- Record 5: 2-D data slab ---
            rec = _read_fortran_record(f)
            slab = np.frombuffer(rec, dtype=">f4").reshape(nlons, nlats).copy()

            fields.append(
                WRFField(
                    hdate=hdate.decode("ascii").strip(),
                    field_name=field_name.decode("ascii").strip(),
                    units=units.decode("ascii").strip(),
                    desc=desc.decode("ascii").strip(),
                    xlvl=float(xlvl),
                    nlons=int(nlons),
                    nlats=int(nlats),
                    slab=slab,
                )
            )

    return fields


# ---------------------------------------------------------------------------
# Comparison logic
# ---------------------------------------------------------------------------


def compare_file_pair(
    ref_path: Path,
    new_path: Path,
    atol: float,
    rtol: float,
) -> tuple[int, int]:
    """Compare two WRF intermediate files field-by-field.

    Returns (n_identical, n_different).
    """
    ref_fields = {f.key: f for f in read_wrf_intermediate(ref_path)}
    new_fields = {f.key: f for f in read_wrf_intermediate(new_path)}

    ref_keys = set(ref_fields)
    new_keys = set(new_fields)

    missing = ref_keys - new_keys
    extra = new_keys - ref_keys

    if missing:
        print(f"  MISSING fields in new file: {sorted(missing)}")
    if extra:
        print(f"  EXTRA fields in new file:   {sorted(extra)}")

    n_identical = 0
    n_different = 0

    for key in sorted(ref_keys & new_keys):
        ref_slab = ref_fields[key].slab.astype(np.float64)
        new_slab = new_fields[key].slab.astype(np.float64)

        max_abs = float(np.max(np.abs(ref_slab - new_slab)))
        ref_mean = float(np.mean(np.abs(ref_slab)))
        max_rel = max_abs / ref_mean if ref_mean > 0 else 0.0

        if max_abs <= atol or np.allclose(ref_slab, new_slab, atol=atol, rtol=rtol):
            n_identical += 1
        else:
            field_label = f"{key[0]} @ {key[1]:.0f} Pa"
            print(f"  DIFF  {field_label:<30}  max_abs={max_abs:.3e}  max_rel={max_rel:.3e}")
            n_different += 1

    return n_identical, n_different


def find_era5_files(directory: Path) -> dict[str, Path]:
    """Return a mapping of filename → Path for ERA5:* files in directory."""
    return {p.name: p for p in sorted(directory.glob("ERA5:*"))}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare two directories of WRF intermediate output files field-by-field.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--ref",
        required=True,
        type=Path,
        metavar="DIR",
        help="Reference output directory (e.g. old code output).",
    )
    parser.add_argument(
        "--new",
        required=True,
        type=Path,
        metavar="DIR",
        help="New output directory to compare against the reference.",
    )
    parser.add_argument(
        "--atol",
        type=float,
        default=0.0,
        help="Absolute tolerance for field values (0 = exact match).",
    )
    parser.add_argument(
        "--rtol",
        type=float,
        default=0.0,
        help="Relative tolerance for field values (0 = exact match).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    ref_files = find_era5_files(args.ref)
    new_files = find_era5_files(args.new)

    if not ref_files:
        print(f"ERROR: no ERA5:* files found in reference directory {args.ref}")
        return 2
    if not new_files:
        print(f"ERROR: no ERA5:* files found in new directory {args.new}")
        return 2

    ref_names = set(ref_files)
    new_names = set(new_files)

    missing_in_new = ref_names - new_names
    extra_in_new = new_names - ref_names

    if missing_in_new:
        print(f"Files present in --ref but missing in --new ({len(missing_in_new)}):")
        for name in sorted(missing_in_new):
            print(f"  {name}")

    if extra_in_new:
        print(f"Files present in --new but missing in --ref ({len(extra_in_new)}):")
        for name in sorted(extra_in_new):
            print(f"  {name}")

    common = sorted(ref_names & new_names)
    print(f"\nComparing {len(common)} file(s) (atol={args.atol}, rtol={args.rtol})\n")

    total_identical = 0
    total_different = 0
    files_with_diffs = 0

    for name in common:
        print(f"{name}")
        n_ok, n_diff = compare_file_pair(ref_files[name], new_files[name], args.atol, args.rtol)
        total_identical += n_ok
        total_different += n_diff
        if n_diff > 0:
            files_with_diffs += 1
        status = "OK" if n_diff == 0 else f"{n_diff} field(s) differ"
        print(f"  -> {n_ok} field(s) identical, {status}\n")

    print("=" * 60)
    print(
        f"TOTAL: {total_identical + total_different} fields compared across {len(common)} file(s)"
    )
    print(f"  Identical : {total_identical}")
    print(f"  Different : {total_different}")
    if total_different == 0 and not missing_in_new:
        print("\nAll outputs are identical.")
        return 0
    else:
        print(f"\nDifferences found in {files_with_diffs} file(s).")
        return 1


if __name__ == "__main__":
    sys.exit(main())
