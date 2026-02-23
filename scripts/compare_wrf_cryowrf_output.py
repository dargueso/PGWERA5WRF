#!/usr/bin/env python
"""compare_wrf_cryowrf_output.py — Compare WRF and CRYOWRF intermediate output.

For a given simulation period the WRF and CRYOWRF pipelines should produce
the same values for every shared field.  CRYOWRF additionally writes two
snow fields (SNOW and SNOWH) that are absent from WRF output.

This script:
  1. Finds matching ERA5:YYYY-MM-DD_HH files in both directories.
  2. Compares every field that appears in both files (shared fields) and
     reports any differences — they should all be identical.
  3. Summarises the CRYOWRF-only fields (SNOW, SNOWH) with basic statistics.

Usage
-----
    python scripts/compare_wrf_cryowrf_output.py \\
        --wrf    /path/to/wrf/output \\
        --cryowrf /path/to/cryowrf/output
"""

from __future__ import annotations

import argparse
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# WRF intermediate binary reader  (shared with compare_wrf_output.py)
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
        return (self.field_name, float(self.xlvl))


def _read_fortran_record(f) -> bytes | None:
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
            rec = _read_fortran_record(f)
            if rec is None:
                break

            rec = _read_fortran_record(f)
            (hdate, _xfcst, _map_source, field_name, units, desc, xlvl, nlons, nlats, _iproj) = (
                struct.unpack(">24sf32s9s25s46sfiii", rec)
            )

            _read_fortran_record(f)  # grid descriptor
            _read_fortran_record(f)  # wind rotation flag

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
# CRYOWRF-only field names
# ---------------------------------------------------------------------------
CRYOWRF_ONLY = {"SNOW", "SNOWH"}


# ---------------------------------------------------------------------------
# Comparison logic
# ---------------------------------------------------------------------------


def compare_file_pair(
    wrf_path: Path,
    cryo_path: Path,
    atol: float,
    rtol: float,
) -> tuple[int, int, list[WRFField]]:
    """Compare a WRF file against a CRYOWRF file.

    Returns (n_identical, n_different, cryowrf_only_fields).
    """
    wrf_fields = {f.key: f for f in read_wrf_intermediate(wrf_path)}
    cryo_fields = {f.key: f for f in read_wrf_intermediate(cryo_path)}

    cryo_only = [f for f in read_wrf_intermediate(cryo_path) if f.field_name in CRYOWRF_ONLY]

    wrf_keys = set(wrf_fields)
    cryo_keys = {k for k in cryo_fields if cryo_fields[k].field_name not in CRYOWRF_ONLY}

    missing_from_cryo = wrf_keys - cryo_keys
    if missing_from_cryo:
        print(f"  WARNING: WRF fields missing from CRYOWRF output: {sorted(missing_from_cryo)}")

    n_identical = 0
    n_different = 0

    for key in sorted(wrf_keys & cryo_keys):
        wrf_slab = wrf_fields[key].slab.astype(np.float64)
        cryo_slab = cryo_fields[key].slab.astype(np.float64)

        max_abs = float(np.max(np.abs(wrf_slab - cryo_slab)))
        wrf_mean = float(np.mean(np.abs(wrf_slab)))
        max_rel = max_abs / wrf_mean if wrf_mean > 0 else 0.0

        if max_abs <= atol or np.allclose(wrf_slab, cryo_slab, atol=atol, rtol=rtol):
            n_identical += 1
        else:
            field_label = f"{key[0]} @ {key[1]:.0f} Pa"
            print(f"  DIFF  {field_label:<30}  max_abs={max_abs:.3e}  max_rel={max_rel:.3e}")
            n_different += 1

    return n_identical, n_different, cryo_only


def print_snow_stats(fields: list[WRFField]) -> None:
    """Print basic statistics for SNOW and SNOWH fields."""
    for f in fields:
        slab = f.slab.astype(np.float64)
        nonzero = slab[slab > 0]
        print(
            f"  {f.field_name:<8} ({f.units})"
            f"  min={slab.min():.4g}  max={slab.max():.4g}"
            f"  mean={slab.mean():.4g}"
            f"  nonzero_pts={nonzero.size}"
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def find_era5_files(directory: Path) -> dict[str, Path]:
    return {p.name: p for p in sorted(directory.glob("ERA5:*"))}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare WRF and CRYOWRF intermediate output for the same period.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--wrf",
        required=True,
        type=Path,
        metavar="DIR",
        help="Directory containing WRF intermediate output files.",
    )
    parser.add_argument(
        "--cryowrf",
        required=True,
        type=Path,
        metavar="DIR",
        help="Directory containing CRYOWRF intermediate output files.",
    )
    parser.add_argument(
        "--atol",
        type=float,
        default=0.0,
        help="Absolute tolerance for shared-field comparison (0 = exact match).",
    )
    parser.add_argument(
        "--rtol",
        type=float,
        default=0.0,
        help="Relative tolerance for shared-field comparison (0 = exact match).",
    )
    parser.add_argument(
        "--snow-stats",
        action="store_true",
        default=False,
        help="Print per-file statistics for CRYOWRF-only snow fields.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    wrf_files = find_era5_files(args.wrf)
    cryo_files = find_era5_files(args.cryowrf)

    if not wrf_files:
        print(f"ERROR: no ERA5:* files found in WRF directory {args.wrf}")
        return 2
    if not cryo_files:
        print(f"ERROR: no ERA5:* files found in CRYOWRF directory {args.cryowrf}")
        return 2

    wrf_names = set(wrf_files)
    cryo_names = set(cryo_files)

    missing = wrf_names - cryo_names
    extra = cryo_names - wrf_names
    if missing:
        print(f"Files in --wrf but not in --cryowrf ({len(missing)}): {sorted(missing)}")
    if extra:
        print(f"Files in --cryowrf but not in --wrf ({len(extra)}): {sorted(extra)}")

    common = sorted(wrf_names & cryo_names)
    print(f"Comparing {len(common)} file(s) (atol={args.atol}, rtol={args.rtol})\n")
    print(f"CRYOWRF-only fields: {', '.join(sorted(CRYOWRF_ONLY))}\n")

    total_identical = 0
    total_different = 0
    files_with_diffs = 0

    for name in common:
        print(f"{name}")
        n_ok, n_diff, snow_fields = compare_file_pair(
            wrf_files[name], cryo_files[name], args.atol, args.rtol
        )
        total_identical += n_ok
        total_different += n_diff
        if n_diff > 0:
            files_with_diffs += 1

        if args.snow_stats and snow_fields:
            print("  CRYOWRF-only fields:")
            print_snow_stats(snow_fields)

        status = "OK" if n_diff == 0 else f"{n_diff} field(s) differ"
        print(f"  -> {n_ok} shared field(s) identical, {status}\n")

    print("=" * 60)
    print(
        f"TOTAL: {total_identical + total_different} shared fields compared "
        f"across {len(common)} file(s)"
    )
    print(f"  Identical : {total_identical}")
    print(f"  Different : {total_different}")

    if total_different == 0 and not missing:
        print("\nAll shared fields (WRF = CRYOWRF) are identical.")
        print(
            f"CRYOWRF adds {len(CRYOWRF_ONLY)} extra field(s) per file: "
            f"{', '.join(sorted(CRYOWRF_ONLY))}"
        )
        print("Re-run with --snow-stats to see snow field statistics.")
        return 0
    else:
        print(f"\nShared-field differences found in {files_with_diffs} file(s).")
        return 1


if __name__ == "__main__":
    sys.exit(main())
