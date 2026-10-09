#!/usr/bin/env python3
"""Generate numbers.txt for the CPU benchmark."""

from __future__ import annotations

import argparse
import random
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a text file with one integer per line.")
    parser.add_argument("--count", type=int, default=2_000_000, help="How many numbers to generate")
    parser.add_argument("--output", type=Path, default=Path("numbers.txt"), help="Output file")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    if args.count <= 0:
        raise SystemExit("--count must be greater than zero")

    rng = random.Random(args.seed)
    with args.output.open("w", encoding="utf-8") as file:
        for _ in range(args.count):
            file.write(f"{rng.randint(1, 1_000_000)}\n")

    print(f"Generated {args.count:,} numbers in {args.output}")


if __name__ == "__main__":
    main()
