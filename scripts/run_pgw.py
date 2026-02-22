#!/usr/bin/env python
"""run_pgw.py — Unified entry point for the pgw4era pipeline.

Write WRF or CRYOWRF intermediate-format boundary condition files from ERA5
data plus CMIP6 climate-change anomalies.

Usage
-----
    python scripts/run_pgw.py --config pgw4era.toml --profile wrf
    python scripts/run_pgw.py --config pgw4era.toml --profile cryowrf
    python scripts/run_pgw.py --config pgw4era.toml --profile cryowrf --overwrite
"""

from __future__ import annotations

import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write WRF/CRYOWRF intermediate-format boundary conditions (PGW).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--config",
        default="pgw4era.toml",
        help="Path to the pgw4era TOML configuration file.",
    )
    parser.add_argument(
        "--profile",
        choices=["wrf", "cryowrf"],
        default="wrf",
        help="Configuration profile to use.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing output files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    from pgw4era.config import load_config

    cfg = load_config(args.config, args.profile)

    if args.profile == "wrf":
        from pgw4era.wrf.write_intermediate import run

        run(cfg, overwrite_file=args.overwrite)

    elif args.profile == "cryowrf":
        one_timestep = getattr(cfg, "one_timestep_files", False)
        if one_timestep:
            from pgw4era.cryowrf.write_intermediate_onetimestep import run
        else:
            from pgw4era.cryowrf.write_intermediate import run
        run(cfg, overwrite_file=args.overwrite)


if __name__ == "__main__":
    main()
