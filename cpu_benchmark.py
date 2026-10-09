#!/usr/bin/env python3
"""Compare sequential, threading and multiprocessing summation of numbers.txt."""

from __future__ import annotations

import argparse
import multiprocessing as mp
import statistics
import threading
import time
from pathlib import Path
from typing import Callable

WORKERS = 4
REPEATS = 3


def byte_ranges(path: Path, workers: int) -> list[tuple[int, int]]:
    """Split a file into approximate byte ranges."""
    size = path.stat().st_size
    step = size // workers
    ranges: list[tuple[int, int]] = []
    start = 0
    for index in range(workers):
        end = size if index == workers - 1 else start + step
        ranges.append((start, end))
        start = end
    return ranges


def sum_range(path_string: str, start: int, end: int) -> int:
    """Sum complete lines whose starting byte offset belongs to [start, end)."""
    total = 0
    path = Path(path_string)

    with path.open("rb") as file:
        if start > 0:
            file.seek(start - 1)
            previous = file.read(1)
            if previous != b"\n":
                file.readline()
        else:
            file.seek(0)

        while True:
            line_start = file.tell()
            if line_start >= end:
                break

            line = file.readline()
            if not line:
                break

            stripped = line.strip()
            if stripped:
                total += int(stripped)

    return total


def sum_sequential(path: Path) -> int:
    return sum_range(str(path), 0, path.stat().st_size)


def sum_threading(path: Path) -> int:
    ranges = byte_ranges(path, WORKERS)
    partials = [0] * WORKERS
    threads: list[threading.Thread] = []

    def worker(index: int, start: int, end: int) -> None:
        partials[index] = sum_range(str(path), start, end)

    for index, (start, end) in enumerate(ranges):
        thread = threading.Thread(target=worker, args=(index, start, end))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return sum(partials)


def sum_multiprocessing(path: Path) -> int:
    ranges = byte_ranges(path, WORKERS)
    tasks = [(str(path), start, end) for start, end in ranges]
    with mp.Pool(processes=WORKERS) as pool:
        return sum(pool.starmap(sum_range, tasks))


def benchmark(name: str, function: Callable[[Path], int], path: Path) -> tuple[int, list[float], float]:
    times: list[float] = []
    result: int | None = None

    for attempt in range(1, REPEATS + 1):
        started = time.perf_counter()
        current = function(path)
        elapsed = time.perf_counter() - started
        times.append(elapsed)

        if result is None:
            result = current
        elif current != result:
            raise RuntimeError(f"{name}: inconsistent sum between runs")

        print(f"{name:20s} run {attempt}: {elapsed:.6f} s")

    assert result is not None
    return result, times, statistics.median(times)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", type=Path, default=Path("numbers.txt"))
    args = parser.parse_args()

    path = args.file.resolve()
    if not path.exists():
        raise SystemExit(f"{path} not found. Run: python generate_numbers.py")

    print(f"File: {path}")
    print(f"Size: {path.stat().st_size / (1024 * 1024):.2f} MiB")
    print(f"Workers: {WORKERS}; repeats: {REPEATS}\n")

    methods = [
        ("Sequential", sum_sequential),
        ("4 threads", sum_threading),
        ("4 processes", sum_multiprocessing),
    ]

    results: list[tuple[str, int, float]] = []
    expected_sum: int | None = None

    for name, function in methods:
        result, _, median = benchmark(name, function, path)
        if expected_sum is None:
            expected_sum = result
        elif result != expected_sum:
            raise RuntimeError(f"{name}: sum differs from the sequential result")
        results.append((name, result, median))
        print()

    print("## CPU benchmark")
    print("| Method | Sum | Median of 3 runs, s |")
    print("|---|---:|---:|")
    for name, result, median in results:
        print(f"| {name} | {result} | {median:.6f} |")


if __name__ == "__main__":
    mp.freeze_support()
    main()
